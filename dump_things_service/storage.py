from __future__ import annotations

import enum
import hashlib
import json
from functools import partial
from itertools import chain
from pathlib import Path
from typing import (
    Any,
    Callable,
    Iterable,
    Literal,
)

import yaml
from fastapi import HTTPException
from pydantic import (
    BaseModel,
    TypeAdapter,
)

from dump_things_service import (
    YAML,
    Format,
)
from dump_things_service.utils import cleaned_json

config_file_name = '.dumpthings.yaml'
token_config_file_name = '.token_config.yaml'  # noqa: S105
ignored_files = {'.', '..', config_file_name}


class MappingMethod(enum.Enum):
    digest_md5 = 'digest-md5'
    digest_md5_p3 = 'digest-md5-p3'
    digest_sha1 = 'digest-sha1'
    digest_sha1_p3 = 'digest-sha1-p3'
    after_last_colon = 'after-last-colon'


class CollectionDirConfig(BaseModel):
    type: Literal['records']
    version: Literal[1]
    schema: str
    format: Literal['yaml']
    idfx: MappingMethod


class TokenPermission(BaseModel):
    curated_read: bool = False
    incoming_read: bool = False
    incoming_write: bool = False


class TokenModes(enum.Enum):
    READ_COLLECTION = 'READ_COLLECTION'
    WRITE_COLLECTION = 'WRITE_COLLECTION'
    READ_SUBMISSIONS = 'READ_SUBMISSIONS'
    WRITE_SUBMISSIONS = 'WRITE_SUBMISSIONS'
    SUBMIT = 'SUBMIT'
    SUBMIT_ONLY = 'SUBMIT_ONLY'
    NOTHING = 'NOTHING'


mode_mapping = {
    TokenModes.READ_COLLECTION: TokenPermission(curated_read=True, incoming_read=True),
    TokenModes.WRITE_COLLECTION: TokenPermission(curated_read=True, incoming_read=True, incoming_write=True),
    TokenModes.READ_SUBMISSIONS: TokenPermission(incoming_read=True),
    TokenModes.WRITE_SUBMISSIONS: TokenPermission(incoming_read=True, incoming_write=True),
    TokenModes.SUBMIT: TokenPermission(curated_read=True, incoming_write=True),
    TokenModes.SUBMIT_ONLY: TokenPermission(incoming_write=True),
    TokenModes.NOTHING: TokenPermission(),
}


class TokenCollectionConfig(BaseModel):
    mode: TokenModes
    incoming_label: str


class TokenConfig(BaseModel):
    user_id: str
    collections: dict[str, TokenCollectionConfig]


class CollectionConfig(BaseModel):
    curated: Path
    incoming: Path | None = None


class GlobalConfig(BaseModel):
    type: Literal['collections']
    version: Literal[1]
    collections: dict[str, CollectionConfig]
    tokens: dict[str, TokenConfig]


def get_hex_digest(hasher: Callable, data: str) -> str:
    hash_context = hasher(data.encode())
    return hash_context.hexdigest()


def mapping_digest_p3(
    hasher: Callable,
    pid: str,
    suffix: str,
) -> Path:
    hex_digest = get_hex_digest(hasher, pid)
    return Path(hex_digest[:3]) / (hex_digest[3:] + '.' + suffix)


def mapping_digest(hasher: Callable, pid: str, suffix: str) -> Path:
    hex_digest = get_hex_digest(hasher, pid)
    return Path(hex_digest + '.' + suffix)


def mapping_after_last_colon(pid: str, suffix: str) -> Path:
    plain_result = pid.split(':')[-1]
    # Escape any colons and slashes in the pid
    escaped_result = (
        plain_result.replace('_', '__').replace('/', '_s').replace('.', '_d')
    )
    return Path(escaped_result + '.' + suffix)


mapping_functions = {
    MappingMethod.digest_md5: partial(mapping_digest, hashlib.md5),
    MappingMethod.digest_md5_p3: partial(mapping_digest_p3, hashlib.md5),
    MappingMethod.digest_sha1: partial(mapping_digest, hashlib.sha1),
    MappingMethod.digest_sha1_p3: partial(mapping_digest_p3, hashlib.sha1),
    MappingMethod.after_last_colon: mapping_after_last_colon,
}


class Storage:
    def __init__(
        self,
        root: str | Path,
    ) -> None:
        from dump_things_service.convert import get_conversion_objects

        self.root = Path(root)
        if not isinstance(self, TokenStorage):
            self.global_config = GlobalConfig(**(self.get_config(self.root)))
            self.collections = self._get_collections()
            self.conversion_objects = get_conversion_objects(self.collections)

    @staticmethod
    def get_config(path: Path, file_name=config_file_name) -> YAML:
        return yaml.load((path / file_name).read_text(), Loader=yaml.SafeLoader)

    def _get_collections(self) -> dict[str, CollectionDirConfig]:
        # read all record collections
        return {
            path.name: CollectionDirConfig(**self.get_config(path))
            for path in self.root.iterdir()
            if path.is_dir() and path not in (Path('.'), Path('.'))
        }

    def get_collection_path(self, collection: str) -> Path:
        collection_path = self.root / collection
        if not collection_path.exists() or not collection_path.is_dir():
            raise HTTPException(
                status_code=404, detail=f'No such collection: "{collection}".'
            )
        return collection_path

    def get_record(
        self, collection: str, pid: str, output_format: Format
    ) -> dict | str | None:
        from dump_things_service.convert import convert_format

        for path in self.get_collection_path(collection).rglob('*'):
            if path.is_file() and path.name not in ignored_files:
                record = yaml.load(path.read_text(), Loader=yaml.SafeLoader)
                if record['pid'] == pid:
                    if output_format == Format.ttl:
                        record = convert_format(
                            target_class=get_class_from_path(path),
                            data=json.dumps(record),
                            input_format=Format.json,
                            output_format=output_format,
                            **self.conversion_objects[collection],
                        )
                    return record
        return None

    def get_all_records(self, collection: str, class_name: str) -> Iterable[dict]:
        for path in (self.get_collection_path(collection) / class_name).rglob('*'):
            if path.is_file() and path.name not in ignored_files:
                yield yaml.load(path.read_text(), Loader=yaml.SafeLoader)


class TokenStorage(Storage):
    def __init__(
        self,
        root: str | Path,
        collection: str,
        canonical_store: Storage,
    ) -> None:
        super().__init__(root)
        self.collection = collection
        self.canonical_store = canonical_store
        self.config = self.get_token_config()

    def get_token_config(self) -> TokenStorageConfig:
        try:
            return TokenStorageConfig(
                **Storage.get_config(self.root, token_config_file_name)
            )
        except FileNotFoundError:
            return TokenStorageConfig(
                read_access=True,
                write_access=True,
            )

    @property
    def conversion_objects(self):
        return self.canonical_store.conversion_objects

    def store_record(
        self,
        *,
        record: BaseModel | str,
        model: Any,
        input_format: Format,
        class_name: str | None = None,
    ) -> list[BaseModel]:
        from dump_things_service.convert import convert_format

        # If the input is ttl, get a JSON object representing the record and
        # convert it to a BaseModel instance.
        if input_format == Format.ttl:
            json_object = cleaned_json(
                json.loads(
                    convert_format(
                        target_class=class_name,
                        data=record,
                        input_format=Format.ttl,
                        output_format=Format.json,
                        **self.canonical_store.conversion_objects[self.collection],
                    )
                )
            )
            record = TypeAdapter(getattr(model, class_name)).validate_python(
                json_object
            )

        final_records = self.extract_inlined(record, model)
        for final_record in final_records:
            self.store_single_record(record=final_record)
        return final_records

    def store_single_record(
        self,
        *,
        record: BaseModel,
    ):
        # Generate the class directory
        class_name = record.__class__.__name__
        record_root = self.root / class_name
        record_root.mkdir(exist_ok=True)

        # Convert the record object into a YAML object
        data = yaml.dump(
            data=record.model_dump(exclude_none=True, mode='json'),
            sort_keys=False,
            allow_unicode=True,
        )

        # Apply the mapping function to the record pid to get the final storage path
        config = self.canonical_store.collections[self.collection]
        storage_path = record_root / mapping_functions[config.idfx](
            pid=record.pid, suffix=config.format
        )

        # Ensure that the storage path is within the record root
        try:
            storage_path.relative_to(record_root)
        except ValueError as e:
            raise HTTPException(status_code=400, detail='Invalid pid.') from e

        # Ensure all intermediate directories exist and save the YAML document
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        storage_path.write_text(data, encoding='utf-8')

    def get_collection_path(self, collection: str) -> Path:
        if self.root.parent.name != collection:
            raise HTTPException(
                status_code=404,
                detail=f'collection "{collection}" does not exist in token space.',
            )
        return self.root

    def extract_inlined(self, record: BaseModel, model: Any) -> list[BaseModel]:
        # The trivial case: no relations
        if not hasattr(record, 'relations') or record.relations is None:
            return [record]

        extracted_sub_records = list(
            chain(
                *[
                    self.extract_inlined(sub_record, model)
                    for sub_record in record.relations.values()
                    # Do not extract 'empty'-Thing records, those are just placeholders
                    if sub_record != model.Thing(pid=sub_record.pid)
                ]
            )
        )
        # Simplify the relations in this record
        new_record = record.model_copy()
        new_record.relations = {
            sub_record_pid: model.Thing(pid=sub_record_pid)
            for sub_record_pid in record.relations
        }
        return [new_record, *extracted_sub_records]


def get_class_from_path(path: Path) -> str | None:
    """Determine the class defined by `path`.

    This code relies on the fact that a `.dumpthings.yaml` exists
    on the same level as the class name.
    """
    if 'token_stores' in path.parts:
        parts = list(path.parts)
        token_store_index = parts.index('token_stores')
        parts[token_store_index] = 'global_store'
        del parts[token_store_index + 2]
        path = Path(*parts)

    while path and path != Path('/'):
        if path.parent.is_dir() and (path.parent / config_file_name).exists():
            return path.stem
        path = path.parent
    return None


def read_token_stores(
    global_store: Storage,
    store_path: Path
) -> dict[str, dict[str, TokenStorage]]:
    return {
        collection.name: {
            token_dir.name: TokenStorage(
                root=token_dir,
                collection=collection.name,
                canonical_store=global_store,
            )
            for token_dir in collection.glob('*')
            if token_dir.is_dir()
        }
        for collection in (store_path / 'token_stores').glob('*')
        if collection.is_dir()
}


def update_token_stores(
        global_store: Storage,
        store_path: Path,
        collection: str,
        token_stores: dict,
) -> int:
    added = 0
    if collection not in token_stores:
        token_stores[collection] = {}
    for element in (store_path / 'token_stores' / collection).glob('*'):
        if element.is_dir() and element.name not in token_stores[collection]:
            token_stores[collection][element.name] = TokenStorage(
                root=element,
                collection=collection,
                canonical_store=global_store,
            )
            added += 1
    return added
