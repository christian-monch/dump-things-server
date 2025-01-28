from __future__ import annotations

import enum
from pathlib import Path
from typing import (
    Literal,
    Optional,
)

import yaml
from pydantic import BaseModel
from yaml import (
    SafeLoader,
    load,
)

from .utils import read_url, create_unique_directory


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


class Storage:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.global_config = GlobalConfig(**(self.get_config(self.root) or dict()))
        self.collections = self._get_collections()

    @staticmethod
    def get_config(path: Path) -> dict|list|str|int|None:
        return yaml.load(
            (path / config_file_name).read_text(),
            Loader=SafeLoader
        )

    def create_schema_collection(
        self,
        schema_url: str,
        mapping_method: MappingMethod = MappingMethod.digest_md5,
    ) -> None:
        # Read the schema
        schema_definition = read_url(schema_url)
        schema = load(schema_definition, Loader=SafeLoader)

        # Check whether a collection for this schema-name and schema-version
        # already exists
        if any([
            config.schema_name == schema['name'] and config.schema_version == schema['version']
            for path, config in self.collections
        ]):
            return

        # Generate a final directory name and write the config file
        final_directory = create_unique_directory(self.root)
        (final_directory / config_file_name).write_text(yaml.dump(
            data={
                'type': 'records',
                'version': 1,
                'schema': schema_url,
                'format': 'yaml',
                'idfx': mapping_method.value,
                'schema_name': schema['name'],
                'schema_version': schema['version']
            },
            sort_keys=False,
        ))

        # Update our knowledge of existing collections
        self.collections = self._get_collections()

    def _get_collections(self) -> list[tuple[Path, CollectionConfig]]:
        # read all record collections
        return [
            (path, CollectionConfig(**self.get_config(path)))
            for path in self.root.iterdir()
            if path.is_dir() and (path / config_file_name).exists()
        ]

    def _get_collection_for_schema(
        self,
        schema_name: str,
        schema_version: str,
    ) -> tuple[Path, CollectionConfig] | None:
        return ([
            (path, config)
            for path, config in self.collections
            if config.schema_name == schema_name and config.schema_version == schema_version
        ] or [None])[0]

    def store_record(
        self,
        schema_url: str,
        schema_name: str,
        schema_version: str,
        record: dict,
    ):
        collection = self._get_collection_for_schema(schema_name, schema_version)
        if collection is None:
            self.create_schema_collection(schema_url)
            raise ValueError('No collection found for schema.')
