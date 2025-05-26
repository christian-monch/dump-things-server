from __future__ import annotations

import dataclasses
import enum
import hashlib
from functools import partial
from pathlib import Path
from typing import (
    Any,
    Callable,
    Literal,
)

import yaml
from pydantic import BaseModel

from dump_things_service.convert import get_conversion_objects
from dump_things_service.model import get_model_for_schema
from dump_things_service.record import RecordDirStore

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
    READ_CURATED = 'READ_CURATED'
    READ_COLLECTION = 'READ_COLLECTION'
    WRITE_COLLECTION = 'WRITE_COLLECTION'
    READ_SUBMISSIONS = 'READ_SUBMISSIONS'
    WRITE_SUBMISSIONS = 'WRITE_SUBMISSIONS'
    SUBMIT = 'SUBMIT'
    SUBMIT_ONLY = 'SUBMIT_ONLY'
    NOTHING = 'NOTHING'


class TokenCollectionConfig(BaseModel):
    mode: TokenModes
    incoming_label: str


class TokenConfig(BaseModel):
    user_id: str
    collections: dict[str, TokenCollectionConfig]


class CollectionConfig(BaseModel):
    default_token: str
    curated: Path
    incoming: Path | None = None


class GlobalConfig(BaseModel):
    type: Literal['collections']
    version: Literal[1]
    collections: dict[str, CollectionConfig]
    tokens: dict[str, TokenConfig]


@dataclasses.dataclass
class InstanceConfig:
    collections: dict = dataclasses.field(default_factory=dict)
    curated_stores: dict = dataclasses.field(default_factory=dict)
    incoming: dict = dataclasses.field(default_factory=dict)
    zones: dict = dataclasses.field(default_factory=dict)
    model_info: dict = dataclasses.field(default_factory=dict)
    token_stores: dict = dataclasses.field(default_factory=dict)
    schemas: dict = dataclasses.field(default_factory=dict)
    conversion_objects: dict = dataclasses.field(default_factory=dict)


mode_mapping = {
    TokenModes.READ_CURATED: TokenPermission(curated_read=True),
    TokenModes.READ_COLLECTION: TokenPermission(curated_read=True, incoming_read=True),
    TokenModes.WRITE_COLLECTION: TokenPermission(
        curated_read=True, incoming_read=True, incoming_write=True
    ),
    TokenModes.READ_SUBMISSIONS: TokenPermission(incoming_read=True),
    TokenModes.WRITE_SUBMISSIONS: TokenPermission(
        incoming_read=True, incoming_write=True
    ),
    TokenModes.SUBMIT: TokenPermission(curated_read=True, incoming_write=True),
    TokenModes.SUBMIT_ONLY: TokenPermission(incoming_write=True),
    TokenModes.NOTHING: TokenPermission(),
}


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


def get_mapping_function(collection_config: CollectionDirConfig):
    return mapping_functions[collection_config.idfx]


def get_permissions(mode: TokenModes) -> TokenPermission:
    return mode_mapping[mode]


class Config:
    @staticmethod
    def get_config_from_file(path: Path) -> GlobalConfig:
        return GlobalConfig(**yaml.load(path.read_text(), Loader=yaml.SafeLoader))

    @staticmethod
    def get_config(path: Path, file_name=config_file_name) -> GlobalConfig:
        return Config.get_config_from_file(path / file_name)

    @staticmethod
    def get_collection_dir_config(
        path: Path, file_name=config_file_name
    ) -> CollectionDirConfig:
        return CollectionDirConfig(
            **yaml.load((path / file_name).read_text(), Loader=yaml.SafeLoader)
        )


def process_config(
        store_path: Path,
        config_file: Path,
        globals_dict: dict[str, Any],
) -> InstanceConfig:

    global_config = Config.get_config_from_file(config_file)
    instance_config = InstanceConfig()
    instance_config.collections = global_config.collections

    # Create a model for each collection, store it in `globals_dict`, and create
    # a `RecordDirStore` for the `curated`-dir in each collection.
    for collection_name, collection_info in global_config.collections.items():

        # Get the config from the curated directory
        collection_config = Config.get_collection_dir_config(store_path / collection_info.curated)

        # Generate the collection model
        model, classes, model_var_name = get_model_for_schema(collection_config.schema)
        instance_config.model_info[collection_name] = model, classes, model_var_name
        globals_dict[model_var_name] = model

        curated_store = RecordDirStore(
            store_path / collection_info.curated, model, get_mapping_function(collection_config)
        )
        instance_config.curated_stores[collection_name] = curated_store
        if collection_info.incoming:
            instance_config.incoming[collection_name] = collection_info.incoming

        instance_config.schemas[collection_name] = collection_config.schema
        if collection_config.schema not in instance_config.conversion_objects:
            instance_config.conversion_objects[collection_config.schema] = get_conversion_objects(collection_config.schema)

    # Create a `RecordDirStore` for each token dir and fetch the permissions
    for token_name, token_info in global_config.tokens.items():
        entry = {'user_id': token_info.user_id, 'collections': {}}
        instance_config.token_stores[token_name] = entry
        for collection_name, token_collection_info in token_info.collections.items():
            entry['collections'][collection_name] = {}
            # A token might be a pure curated read token, i.e., have the mode
            # `READ_COLLECTION`. In this case there might be no incoming store.
            if collection_name in instance_config.incoming:
                if collection_name not in instance_config.zones:
                    instance_config.zones[collection_name] = {}
                instance_config.zones[collection_name][token_name] = token_collection_info.incoming_label
                model = instance_config.curated_stores[collection_name].model
                mapping_function = instance_config.curated_stores[collection_name].pid_mapping_function
                # Ensure that the store directory exists
                store_dir = (
                        store_path
                        / instance_config.incoming[collection_name]
                        / token_collection_info.incoming_label
                )
                store_dir.mkdir(parents=True, exist_ok=True)
                token_store = RecordDirStore(store_dir, model, mapping_function)
                entry['collections'][collection_name]['store'] = token_store
            entry['collections'][collection_name]['permissions'] = get_permissions(
                token_collection_info.mode
            )
    return instance_config
