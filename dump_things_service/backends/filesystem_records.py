from __future__ import annotations

import dataclasses
import enum
import hashlib
from functools import partial
from itertools import chain
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Literal,
)

import yaml
from fastapi import HTTPException
from pydantic import (
    BaseModel,
)

from dump_things_service.backends.interface import (
    AuthorizationError,
    CollectionInfo,
    StorageBackendInterface,
    UnknownClassError,
    UnknownCollectionError,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from dump_things_service import YAML


config_file_name = '.dumpthings.yaml'
ignored_files = {'.', '..', config_file_name}
ignored_paths = set(map(Path, ignored_files))


@dataclasses.dataclass
class RecordInfo:
    record: dict
    class_name: str


class GlobalConfig(BaseModel):
    type: Literal['collections']
    version: Literal[1]


class MappingMethod(enum.Enum):
    digest_md5 = 'digest-md5'
    digest_md5_p3 = 'digest-md5-p3'
    digest_sha1 = 'digest-sha1'
    digest_sha1_p3 = 'digest-sha1-p3'
    after_last_colon = 'after-last-colon'


class CollectionConfig(BaseModel):
    type: Literal['records']
    version: Literal[1]
    schema: str
    format: Literal['yaml']
    idfx: MappingMethod


def get_hex_digest(hasher: Callable, data: str) -> str:
    hash_context = hasher(data.encode())
    return hash_context.hexdigest()


def mapping_digest_p3(
    hasher: Callable,
    identifier: str,
    suffix: str,
) -> Path:
    hex_digest = get_hex_digest(hasher, identifier)
    return Path(hex_digest[:3]) / (hex_digest[3:] + '.' + suffix)


def mapping_digest(hasher: Callable, identifier: str, suffix: str) -> Path:
    hex_digest = get_hex_digest(hasher, identifier)
    return Path(hex_digest + '.' + suffix)


def mapping_after_last_colon(identifier: str, suffix: str) -> Path:
    plain_result = identifier.split(':')[-1]
    # Escape any colons and slashes in the identifier
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


class FileSystemRecords(StorageBackendInterface):
    def __init__(self, root: str | Path) -> None:
        super().__init__()
        self.global_store = None
        self.root = Path(root)
        self.global_store = Storage(self.root / 'global_store')
        self.collections.update(
            [
                (
                    path.name,
                    CollectionInfo(schema_location=self._get_config(path)['schema']),
                )
                for path in (self.root / 'global_store').iterdir()
                if path.is_dir() and path not in ignored_paths
            ]
        )
        self.token_stores = {
            path.name: TokenStorage(path, self.global_store)
            for path in (self.root / 'token_stores').glob('*')
            if path.is_dir()
        }

    @staticmethod
    def _get_config(path: Path) -> YAML:
        return yaml.load((path / config_file_name).read_text(), Loader=yaml.SafeLoader)

    def _update_token_stores(self) -> int:
        """Add new token stores for newly create token store directories"""
        added = 0
        for element in (self.root / 'token_stores').glob('*'):
            if element.is_dir() and element.name not in self.token_stores:
                self.token_stores[element.name] = TokenStorage(
                    element, self.global_store
                )
                added += 1
        return added

    def _get_store_for_token(
        self,
        token: str,
    ) -> TokenStorage:
        # If no corresponding token store is found, update the token stores
        store = self.token_stores.get(token, None)
        if not store:
            self._update_token_stores()

        # If still no corresponding token store is found, the token is not valid
        store = self.token_stores.get(token, None)
        if not store:
            msg = f'Invalid authorization token: {token}'
            raise AuthorizationError(msg)
        return store

    @staticmethod
    def _check_token(token: Any) -> None:
        if token is None:
            msg = 'Authorization token is required.'
            raise AuthorizationError(msg)
        if not isinstance(token, str):
            msg = 'Authorization token must be a string.'
            raise AuthorizationError(msg)

    def _create_result(self, collection: str, record_info: RecordInfo):
        constructor = getattr(
            self.collections[collection].model, record_info.class_name
        )
        return constructor(**record_info.record)

    def _check_collection(self, collection: str) -> None:
        if collection not in self.collections:
            msg = f'No such collection: {collection}'
            raise UnknownCollectionError(msg)

    def store(
        self,
        collection: str,
        record: BaseModel,
        authorization_info: Any,
    ) -> list[BaseModel]:
        self._check_token(authorization_info)
        self._check_collection(collection)

        store = self._get_store_for_token(authorization_info)
        return store.store_record(
            record=record,
            collection=collection,
            model=self.collections[collection].model,
        )

    def record_with_id(
        self,
        collection: str,
        identifier: str,
        authorization_info: Any | None = None,
    ) -> BaseModel | None:
        if authorization_info:
            self._check_token(authorization_info)
        self._check_collection(collection)

        record_info = None
        if authorization_info:
            store = self._get_store_for_token(authorization_info)
            record_info = store.get_record(collection, identifier)
        if not record_info:
            record_info = self.global_store.get_record(collection, identifier)
        if record_info:
            return self._create_result(collection, record_info)
        return None

    def records_of_class(
        self, collection: str, class_name: str, authorization_info: Any | None = None
    ) -> Iterable[BaseModel]:
        if authorization_info:
            self._check_token(authorization_info)
        self._check_collection(collection)

        collection_info = self.collections[collection]
        if class_name not in collection_info.classes:
            msg = f'Unknown class: {class_name}'
            raise UnknownClassError(msg)

        record_infos = {}
        for search_class_name in collection_info.classes[class_name]:
            for record_info in self.global_store.get_all_records(
                collection, search_class_name
            ):
                record_infos[record_info.record['id']] = record_info
        if authorization_info:
            store = self._get_store_for_token(authorization_info)
            for search_class_name in collection_info.classes[class_name]:
                for record_info in store.get_all_records(collection, search_class_name):
                    record_infos[record_info.record['id']] = record_info
        return [
            self._create_result(collection, record_info)
            for record_info in record_infos.values()
        ]


class Storage:
    def __init__(
        self,
        root: str | Path,
    ) -> None:
        self.root = Path(root)
        if not isinstance(self, TokenStorage):
            self.global_config = GlobalConfig(**(self.get_config(self.root)))
            self.collections = self._get_collections()

    @staticmethod
    def get_config(path: Path) -> YAML:
        return yaml.load((path / config_file_name).read_text(), Loader=yaml.SafeLoader)

    def _get_collections(self) -> dict[str, CollectionConfig]:
        # read all record collections
        return {
            path.name: CollectionConfig(**self.get_config(path))
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

    def get_record(self, collection: str, identifier: str) -> RecordInfo | None:
        for path in self.get_collection_path(collection).rglob('*'):
            if path.is_file() and path.name not in ignored_files:
                record = yaml.load(path.read_text(), Loader=yaml.SafeLoader)
                if record['id'] == identifier:
                    return RecordInfo(
                        record=record,
                        class_name=get_class_from_path(path),
                    )
        return None

    def get_all_records(self, collection: str, class_name: str) -> list[RecordInfo]:
        for path in (self.get_collection_path(collection) / class_name).rglob('*'):
            if path.is_file() and path.name not in ignored_files:
                yield RecordInfo(
                    record=yaml.load(path.read_text(), Loader=yaml.SafeLoader),
                    class_name=get_class_from_path(path),
                )


class TokenStorage(Storage):
    def __init__(
        self,
        root: str | Path,
        canonical_store: Storage,
    ) -> None:
        super().__init__(root)
        self.canonical_store = canonical_store

    def store_record(
        self,
        *,
        record: BaseModel,
        collection: str,
        model: Any,
    ) -> list[BaseModel]:
        final_records = self.extract_inlined(record, model)
        for final_record in final_records:
            self.store_single_record(
                record=final_record,
                collection=collection,
            )
        return final_records

    def store_single_record(
        self,
        *,
        record: BaseModel,
        collection: str,
    ):
        # Generate the class directory
        class_name = record.__class__.__name__
        record_root = self.get_collection_path(collection) / class_name
        record_root.mkdir(exist_ok=True)

        # Convert the record object into a YAML object
        data = yaml.dump(data=record.model_dump(exclude_none=True), sort_keys=False)

        # Apply the mapping function to the record id to get the final storage path
        config = self.canonical_store.collections[collection]
        storage_path = record_root / mapping_functions[config.idfx](
            identifier=record.id, suffix=config.format
        )

        # Ensure that the storage path is within the record root
        try:
            storage_path.relative_to(record_root)
        except ValueError as e:
            raise HTTPException(status_code=400, detail='Invalid identifier.') from e

        # Ensure all intermediate directories exist and save the yaml document
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        storage_path.write_text(data)

    def get_collection_path(self, collection: str) -> Path:
        collection_path = self.root / collection
        if not collection_path.exists():
            # This will raise if the canonical store does not have the collection
            self.canonical_store.get_collection_path(collection)
            collection_path.mkdir(parents=True)
        elif not collection_path.is_dir():
            raise HTTPException(
                status_code=404, detail=f'{collection_path} is not a directory.'
            )
        return collection_path

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
                    if sub_record != model.Thing(id=sub_record.id)
                ]
            )
        )
        # Simplify the relations in this record
        new_record = record.model_copy()
        new_record.relations = {
            sub_record_id: model.Thing(id=sub_record_id)
            for sub_record_id in record.relations
        }
        return [new_record, *extracted_sub_records]


def get_class_from_path(path: Path) -> str | None:
    """Determine the class that is defined by `path`.

    This code relies on the fact that a `.dumpthings.yaml` exists
    on the same level as the class name.
    """
    if 'token_stores' in path.parts:
        parts = list(path.parts)
        token_store_index = parts.index('token_stores')
        parts[token_store_index : token_store_index + 2] = ['global_store']
        path = Path(*parts)

    while path and path != Path('/'):
        if path.parent.is_dir() and (path.parent / config_file_name).exists():
            return path.stem
        path = path.parent
    return None
