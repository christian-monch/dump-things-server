from __future__ import annotations

import enum
import hashlib
from functools import partial
from pathlib import Path
from typing import (
    Callable,
    Literal,
    Union,
)

import yaml
from fastapi import HTTPException
from pydantic import BaseModel
from yaml import (
    SafeLoader,
    load,
)

from .utils import read_url


YAML = Union[int, float, str, dict, list, None]


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
    return Path(identifier.split(':')[-1] + '.' + suffix)


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
        self.root = Path(root)
        self.global_config = GlobalConfig(**(self.get_config(self.root)))
        self.collections = self._get_collections()

    @staticmethod
    def get_config(path: Path) -> YAML:
        return yaml.load(
            (path / config_file_name).read_text(),
            Loader=SafeLoader
        )

    @staticmethod
    def _read_schema(schema_id: str) -> YAML:
        schema_definition = read_url(schema_id)
        return load(schema_definition, Loader=SafeLoader)

    def _get_collections(self) -> dict[str, CollectionConfig]:
        # read all record collections
        return {
            path.name: CollectionConfig(**self.get_config(path))
            for path in self.root.iterdir()
            if path.is_dir() and path not in (Path('.'), Path('.'))
        }

    def store_record(
        self,
        *,
        record: BaseModel,
        label: str,
    ):
        # Generate the class directory
        record_root = self._get_label_path(label) / type(record).__name__
        record_root.mkdir(exist_ok=True)

        # Get the yaml document representing the record
        data = yaml.dump(data=record.model_dump(), sort_keys=False)

        # Apply the mapping function to get the final storage path
        config = self.collections[label]
        storage_path = record_root / mapping_functions[config.idfx](
            identifier=record.id,
            data=data,
            suffix=config.format
        )

        # Ensure all intermediate directories exist and save the yaml document
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        storage_path.write_text(data)

    def _get_label_path(self, label: str) -> Path:
        label_path = self.root / label
        if not label_path.exists() or not label_path.is_dir():
            raise HTTPException(status_code=404, detail=f'Application {label} not found.')
        return label_path

    def get_record(self, label: str, identifier: str) -> dict | None:
        for path in self._get_label_path(label).rglob('*'):
            if path.is_file() and path.name not in ignored_files:
                record = yaml.load(path.read_text(), Loader=SafeLoader)
                if record['id'] == identifier:
                    return record

    def get_all_records(self, label: str, type_name: str) -> list[dict]:
        for path in (self._get_label_path(label) / type_name).rglob('*'):
            if path.is_file() and path.name not in ignored_files:
                yield yaml.load(path.read_text(), Loader=SafeLoader)
