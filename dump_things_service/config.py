from __future__ import annotations

import dataclasses
import enum
import hashlib
from functools import partial
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
    ValidationError,
)
from yaml.scanner import ScannerError

from dump_things_service import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)
from dump_things_service.convert import get_conversion_objects
from dump_things_service.model import get_model_for_schema

if TYPE_CHECKING:
    import types

    from dump_things_service.record import RecordDirStore


config_file_name = '.dumpthings.yaml'
token_config_file_name = '.token_config.yaml'  # noqa: S105
ignored_files = {'.', '..', config_file_name}


class ConfigError(Exception):
    pass


class MappingMethod(enum.Enum):
    digest_md5 = 'digest-md5'
    digest_md5_p3 = 'digest-md5-p3'
    digest_md5_p3_p3 = 'digest-md5-p3-p3'
    digest_sha1 = 'digest-sha1'
    digest_sha1_p3 = 'digest-sha1-p3'
    digest_sha1_p3_p3 = 'digest-sha1-p3-p3'
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
    store_path: Path
    collections: dict = dataclasses.field(default_factory=dict)
    stores: dict = dataclasses.field(default_factory=dict)
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


def mapping_digest_p3_p3(
        hasher: Callable,
        pid: str,
        suffix: str,
) -> Path:
    hex_digest = get_hex_digest(hasher, pid)
    return Path(hex_digest[:3]) / hex_digest[3:6] / (hex_digest[6:] + '.' + suffix)


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
    MappingMethod.digest_md5_p3_p3: partial(mapping_digest_p3_p3, hashlib.md5),
    MappingMethod.digest_sha1: partial(mapping_digest, hashlib.sha1),
    MappingMethod.digest_sha1_p3: partial(mapping_digest_p3, hashlib.sha1),
    MappingMethod.digest_sha1_p3_p3: partial(mapping_digest_p3_p3, hashlib.sha1),
    MappingMethod.after_last_colon: mapping_after_last_colon,
}


def get_mapping_function(collection_config: CollectionDirConfig):
    return mapping_functions[collection_config.idfx]


def get_permissions(mode: TokenModes) -> TokenPermission:
    return mode_mapping[mode]


class Config:
    @staticmethod
    def get_config_from_file(path: Path) -> GlobalConfig:
        try:
            return GlobalConfig(**yaml.load(path.read_text(), Loader=yaml.SafeLoader))
        except ScannerError as e:
            msg = f'YAML-error while reading config file {path}: {e}'
            raise ConfigError(msg) from e
        except TypeError:
            msg = f'Error in yaml file {path}: content is not a mapping'
            raise ConfigError(msg) from None
        except ValidationError as e:
            msg = f'Pydantic-error reading config file {path}: {e}'
            raise ConfigError(msg) from e

    @staticmethod
    def get_config(path: Path, file_name=config_file_name) -> GlobalConfig:
        return Config.get_config_from_file(path / file_name)

    @staticmethod
    def get_collection_dir_config(
        path: Path,
        file_name: str = config_file_name,
    ) -> CollectionDirConfig:
        config_path = path / file_name
        try:
            return CollectionDirConfig(
                **yaml.load(config_path.read_text(), Loader=yaml.SafeLoader)
            )
        except ScannerError as e:
            msg = f'YAML-error while reading config file {config_path}: {e}'
            raise ConfigError(msg) from e
        except ValidationError as e:
            msg = f'Pydantic-error reading config file {config_path}: {e}'
            raise ConfigError(msg) from e


def process_config(
        store_path: Path,
        config_file: Path,
        globals_dict: dict[str, Any],
) -> InstanceConfig:

    config_object = Config.get_config_from_file(config_file)
    return process_config_object(
        store_path=store_path,
        config_object=config_object,
        globals_dict=globals_dict,
    )


def process_config_object(
    store_path: Path,
    config_object: GlobalConfig,
    globals_dict: dict[str, Any],
):
    from dump_things_service.record import get_record_dir_store

    instance_config = InstanceConfig(store_path=store_path)
    instance_config.collections = config_object.collections

    # Create a model for each collection, store it in `globals_dict`, and create
    # a `RecordDirStore` for the `curated`-dir in each collection.
    for collection_name, collection_info in config_object.collections.items():

        # Get the config from the curated directory
        collection_config = Config.get_collection_dir_config(store_path / collection_info.curated)

        # Generate the collection model
        model, classes, model_var_name = get_model_for_schema(collection_config.schema)
        instance_config.model_info[collection_name] = model, classes, model_var_name
        globals_dict[model_var_name] = model

        curated_store = get_record_dir_store(
            instance_config=instance_config,
            root=store_path / collection_info.curated,
            model=model,
            pid_mapping_function=get_mapping_function(collection_config),
            suffix=collection_config.format,
        )
        instance_config.curated_stores[collection_name] = curated_store
        if collection_info.incoming:
            instance_config.incoming[collection_name] = collection_info.incoming

        instance_config.schemas[collection_name] = collection_config.schema
        if collection_config.schema not in instance_config.conversion_objects:
            instance_config.conversion_objects[collection_config.schema] = get_conversion_objects(collection_config.schema)

    # Create a `RecordDirStore` for each token dir and fetch the permissions
    for token_name, token_info in config_object.tokens.items():
        entry = {'user_id': token_info.user_id, 'collections': {}}
        instance_config.token_stores[token_name] = entry
        for collection_name, token_collection_info in token_info.collections.items():
            entry['collections'][collection_name] = {}

            # A token might be a pure curated read token, i.e., have the mode
            # `READ_COLLECTION`. In this case there might be no incoming store.
            if (
                    collection_name in instance_config.incoming and
                    token_collection_info.mode not in (
                        TokenModes.READ_CURATED,
                        TokenModes.NOTHING,
                    )
            ):
                # Check that the incoming label is set for a token that has
                # access rights to incoming records.
                if not token_collection_info.incoming_label:
                    msg = f'Token `{token_name}` with mode {token_collection_info.mode} must not have an empty `incoming_label`'
                    raise ConfigError(msg)

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
                token_store = get_record_dir_store(
                    instance_config=instance_config,
                    root=store_dir,
                    model=model,
                    pid_mapping_function=mapping_function,
                    suffix=instance_config.curated_stores[collection_name].suffix,
                )
                entry['collections'][collection_name]['store'] = token_store
            entry['collections'][collection_name]['permissions'] = get_permissions(
                token_collection_info.mode
            )
    return instance_config


def get_token_store(
        instance_config: InstanceConfig,
        collection_name: str, token: str
) -> tuple[RecordDirStore, TokenPermission] | tuple[None, None]:
    if collection_name not in instance_config.curated_stores:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f'No such collection: "{collection_name}".',
        )
    if token not in instance_config.token_stores:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail='Invalid token.')

    token_store = None
    token_collection_info = instance_config.token_stores[token]['collections'][collection_name]
    permissions = token_collection_info['permissions']
    if permissions.incoming_write or permissions.incoming_read:
        token_store = token_collection_info.get('store')
        if not token_store:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f'Configuration does not define an incoming store for token "{token}" in collection "{collection_name}".',
            )
    return token_store, permissions


def get_default_token_name(
        instance_config: InstanceConfig,
        collection: str
) -> str:
    if collection not in instance_config.collections:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail=f'No such collection: {collection}'
        )
    return instance_config.collections[collection].default_token


def join_default_token_permissions(
        instance_config: InstanceConfig,
        permissions: TokenPermission,
        collection: str,
) -> TokenPermission:
    default_token_name = instance_config.collections[collection].default_token
    default_token_permissions = instance_config.token_stores[default_token_name]['collections'][collection]['permissions']
    result = TokenPermission()
    result.curated_read = permissions.curated_read | default_token_permissions.curated_read
    result.incoming_read = permissions.incoming_read | default_token_permissions.incoming_read
    result.incoming_write = permissions.incoming_write | default_token_permissions.incoming_write
    return result


def get_zone(
        instance_config: InstanceConfig,
        collection: str,
        token: str,
) -> str | None:
    """Get the zone for the given collection and token."""
    if collection not in instance_config.zones:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail=f'No incoming zone defined for collection: {collection}'
        )
    if token not in instance_config.zones[collection]:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail=f'No incoming zone defined for collection: {collection}'
        )
    return instance_config.zones[collection][token]


def get_conversion_objects_for_collection(
    instance_config: InstanceConfig,
    collection_name: str,
) -> dict:
    """Get the conversion objects for the given collection."""
    if collection_name not in instance_config.schemas:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail=f'No such collection: {collection_name}'
        )
    return instance_config.conversion_objects[instance_config.schemas[collection_name]]


def get_model_info_for_collection(
    instance_config: InstanceConfig,
    collection_name: str,
) -> tuple[types.ModuleType, dict[str, Any], str]:
    if collection_name not in instance_config.model_info:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail=f'No such collection: {collection_name}'
        )
    return instance_config.model_info[collection_name]
