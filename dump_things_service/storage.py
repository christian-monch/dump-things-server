from __future__ import annotations

import enum
import hashlib
import json
from functools import partial
from pathlib import Path
from typing import (
    Callable,
    Literal,
)

import yaml
from fastapi import HTTPException
from pydantic import BaseModel

from . import (
    Format,
    YAML,
)
from .convert import convert_format
from .utils import cleaned_json

config_file_name = '.dumpthings.yaml'
ignored_files = {'.', '..', config_file_name}


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


def mapping_digest_p3(hasher: Callable, identifier: str, data: str, suffix: str) -> Path:
    hex_digest = get_hex_digest(hasher, data)
    return Path(hex_digest[:3]) / (hex_digest[3:] + '.' + suffix)


def mapping_digest(hasher: Callable, identifier: str, data: str, suffix: str) -> Path:
    hex_digest = get_hex_digest(hasher, data)
    return Path(hex_digest + '.' + suffix)


def mapping_after_last_colon(identifier: str, data: str, suffix: str) -> Path:
    plain_result = identifier.split(':')[-1]
    # Escape any colons and slashes in the identifier
    escaped_result = plain_result.replace('_', '__').replace('/', '_s').replace('.', '_d')
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
        from .convert import get_conversion_objects

        self.root = Path(root)
        if not isinstance(self, TokenStorage):
            self.global_config = GlobalConfig(**(self.get_config(self.root)))
            self.collections = self._get_collections()
            self.conversion_objects = get_conversion_objects(self.collections)

    @staticmethod
    def get_config(path: Path) -> YAML:
        return yaml.load(
            (path / config_file_name).read_text(),
            Loader=yaml.SafeLoader
        )

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
            raise HTTPException(status_code=404, detail=f'Application {collection} not found.')
        return collection_path

    def get_record(self, collection: str, identifier: str, format: Format) -> dict | str | None:
        from .convert import convert_format

        for path in self.get_collection_path(collection).rglob('*'):
            if path.is_file() and path.name not in ignored_files:
                record = yaml.load(path.read_text(), Loader=yaml.SafeLoader)
                if record['id'] == identifier:
                    if format == Format.ttl:
                        record = convert_format(
                            target_class=get_class_from_path(path),
                            data=json.dumps(record),
                            input_format=Format.json,
                            output_format=format,
                            **self.conversion_objects[collection]
                        )
                    return record

    def get_all_records(self, collection: str, class_name: str) -> list[dict]:
        for path in (self.get_collection_path(collection) / class_name).rglob('*'):
            if path.is_file() and path.name not in ignored_files:
                yield yaml.load(path.read_text(), Loader=yaml.SafeLoader)


class TokenStorage(Storage):
    def __init__(
        self,
        root: str | Path,
        canonical_store: Storage,
    ) -> None:
        super().__init__(root)
        self.canonical_store = canonical_store

    @property
    def conversion_objects(self):
        return self.canonical_store.conversion_objects

    def store_record(
            self,
            *,
            record: BaseModel | str,
            collection: str,
            class_name: str,
            format: Format,
    ):
        # Generate the class directory
        record_root = self.get_collection_path(collection) / class_name
        record_root.mkdir(exist_ok=True)

        # Get the yaml document representing the record
        if format == Format.ttl:
            json_object = cleaned_json(
                json.loads(
                    convert_format(
                        target_class=class_name,
                        data=record,
                        input_format=Format.ttl,
                        output_format=Format.json,
                        **self.canonical_store.conversion_objects[collection],
                    )
                )
            )
            identifier = json_object['id']
            data = yaml.dump(data=json_object, sort_keys=False)
        else:
            identifier = record.id
            data = yaml.dump(
                data=record.model_dump(exclude_none=True),
                sort_keys=False,
            )

        # Apply the mapping function to get the final storage path
        config = self.canonical_store.collections[collection]
        storage_path = record_root / mapping_functions[config.idfx](
            identifier=identifier,
            data=data,
            suffix=config.format
        )

        # Ensure that the storage path is within the record root
        try:
            storage_path.relative_to(record_root)
        except ValueError:
            raise HTTPException(status_code=400, detail='Invalid identifier.')

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
            raise HTTPException(status_code=404, detail=f'{collection_path} is not a directory.')
        return collection_path


def get_class_from_path(path: Path) -> str:
    """Determine the class that is defined by `path`.

    This code relies on the fact that a `.dumpthings.yaml` exists
    on the same level as the class name.
    """
    if 'token_stores' in path.parts:
        parts = list(path.parts)
        token_store_index = parts.index('token_stores')
        parts[token_store_index:token_store_index + 2] = ['global_store']
        path = Path(*parts)

    while path and path != Path('/'):
        if path.parent.is_dir() and (path.parent / config_file_name).exists():
            return path.stem
        path = path.parent
