from __future__ import annotations

import enum
import hashlib
from functools import partial
from pathlib import Path
from typing import (
    Literal,
    Optional,
    Union,
)

import yaml
from pydantic import BaseModel
from yaml import (
    SafeLoader,
    load,
)

from .utils import read_url, create_unique_directory


YAML = Union[int, float, str, dict, list, None]


config_file_name = '.dumpthings.yaml'


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
    schema_name: Optional[str] = ''
    schema_version: Optional[str] = ''


def mapping_digest_sha1_p3(data: str, suffix: str) -> Path:
    hash_context = hashlib.sha1(data.encode())
    hex_digest = hash_context.hexdigest()
    return Path(hex_digest[:3]) / (hex_digest[3:] + '.' + suffix)


def mapping_digest_sha1(data: str, suffix: str) -> Path:
    hash_context = hashlib.sha1(data.encode())
    hex_digest = hash_context.hexdigest()
    return Path(hex_digest + '.' + suffix)


def mapping_digest_md5_p3(data: str, suffix: str) -> Path:
    hash_context = hashlib.md5(data.encode())
    hex_digest = hash_context.hexdigest()
    return Path(hex_digest[:3]) / (hex_digest[3:] + '.' + suffix)


def mapping_digest_md5(data: str, suffix: str) -> Path:
    hash_context = hashlib.md5(data.encode())
    hex_digest = hash_context.hexdigest()
    return Path(hex_digest + '.' + suffix)


def not_implemented(method: str, data: str, suffix: str) -> Path:
    msg = f'Mapping method {method} not yet implemented'
    raise NotImplementedError(msg)


mapping_functions = {
    MappingMethod.digest_md5: mapping_digest_md5,
    MappingMethod.digest_md5_p3: mapping_digest_md5_p3,
    MappingMethod.digest_sha1: mapping_digest_sha1,
    MappingMethod.digest_sha1_p3: mapping_digest_sha1_p3,
    MappingMethod.after_last_colon: partial(not_implemented, 'after_last_colon'),
}


class Storage:
    def __init__(
        self,
        root: str | Path,
        *,
        create_new_ok: bool = False
    ) -> None:
        self.root = Path(root)
        if not self.root.exists() and create_new_ok:
            self.root.mkdir(parents=True)
            (self.root / config_file_name).write_text('type: collections\nversion: 1\n')
        self.global_config = GlobalConfig(**(self.get_config(self.root) or dict()))
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

    def create_schema_collection(
        self,
        schema_id: str,
        mapping_method: MappingMethod = MappingMethod.digest_sha1_p3,
    ) -> tuple[Path, CollectionConfig]:
        # If the collection does not already exists, create it
        collection = self._get_collection_for_schema(schema_id)
        if collection is None:
            # Read the schema
            schema = self._read_schema(schema_id)

            # Generate a final directory name and write the config file
            final_directory = create_unique_directory(self.root)
            (final_directory / config_file_name).write_text(yaml.dump(
                data={
                    'type': 'records',
                    'version': 1,
                    'schema': schema_id,
                    'format': 'yaml',
                    'idfx': mapping_method.value,
                    'schema_name': schema['name'],
                    'schema_version': schema['version']
                },
                sort_keys=False,
            ))

            # Update our knowledge of existing collections
            self.collections = self._get_collections()

        return self._get_collection_for_schema(schema_id)

    def _get_collections(self) -> list[tuple[Path, CollectionConfig]]:
        # read all record collections
        return [
            (path, CollectionConfig(**self.get_config(path)))
            for path in self.root.iterdir()
            if path.is_dir() and (path / config_file_name).exists()
        ]

    def _get_collection_for_schema(
        self,
        schema_id: str,
    ) -> tuple[Path, CollectionConfig] | None:
        return ([
            (path, config)
            for path, config in self.collections
            if config.schema == schema_id
        ] or [None])[0]

    def store_record(
        self,
        *,
        record: BaseModel,
        schema_id: str,
    ):
        # Get the collection, if it does not yet exist, create it
        collection = self._get_collection_for_schema(schema_id)
        if collection is None:
            collection = self.create_schema_collection(schema_id)

        # Generate the class directory
        path, config = collection
        record_root = path / type(record).__name__
        record_root.mkdir(exist_ok=True)

        # Get the yaml document representing the record
        data = yaml.dump(data=record.model_dump(), sort_keys=False)

        # Apply the mapping function to get the final storage path
        storage_path = record_root / mapping_functions[config.idfx](
            data=data,
            suffix=config.format
        )

        # Ensure all intermediate directories exist and save the yaml document
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        storage_path.write_text(data)
