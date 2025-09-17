from __future__ import annotations

import dataclasses
import enum
import hashlib
import logging
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
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)
from dump_things_service.auth import AuthenticationError
from dump_things_service.backends.record_dir import RecordDirStore
from dump_things_service.backends.schema_type_layer import SchemaTypeLayer
from dump_things_service.backends.sqlite import SQLiteBackend
from dump_things_service.backends.sqlite import (
    record_file_name as sqlite_record_file_name,
)
from dump_things_service.converter import get_conversion_objects
from dump_things_service.model import get_model_for_schema
from dump_things_service.store.model_store import ModelStore
from dump_things_service.token import TokenPermission

if TYPE_CHECKING:
    import types

logger = logging.getLogger('uvicorn')

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


class BackendConfigRecordDir(BaseModel):
    type: Literal['record_dir', 'record_dir+stl']


class BackendConfigSQLite(BaseModel):
    type: Literal['sqlite', 'sqlite+stl']
    schema: str


class ForgejoAuthConfig(BaseModel):
    type: Literal['forgejo']
    url: str
    organization: str
    team: str
    label_type: Literal['team', 'user']
    repository: str | None = None


class ConfigAuthConfig(BaseModel):
    type: Literal['config'] = 'config'


class CollectionConfig(BaseModel):
    default_token: str
    curated: Path
    incoming: Path | None = None
    backend: BackendConfigRecordDir | BackendConfigSQLite | None = None
    auth_sources: list[ForgejoAuthConfig | ConfigAuthConfig] = [ConfigAuthConfig()]


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
    permissions: dict = dataclasses.field(default_factory=dict)
    model_info: dict = dataclasses.field(default_factory=dict)
    token_stores: dict = dataclasses.field(default_factory=dict)
    schemas: dict = dataclasses.field(default_factory=dict)
    conversion_objects: dict = dataclasses.field(default_factory=dict)
    backend: dict = dataclasses.field(default_factory=dict)
    auth_providers: dict = dataclasses.field(default_factory=dict)
    tokens: dict = dataclasses.field(default_factory=dict)


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


def get_mapping_function_by_name(mapping_function_name: str) -> Callable:
    return mapping_functions[MappingMethod(mapping_function_name)]


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
        if not config_path.exists():
            msg = f'Config file does not exist: {config_path}'
            raise ConfigError(msg)
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
    order_by: list[str],
    globals_dict: dict[str, Any],
) -> InstanceConfig:
    config_object = Config.get_config_from_file(config_file)
    return process_config_object(
        store_path=store_path,
        config_object=config_object,
        order_by=order_by,
        globals_dict=globals_dict,
    )


def process_config_object(
    store_path: Path,
    config_object: GlobalConfig,
    order_by: list[str],
    globals_dict: dict[str, Any],
):
    from dump_things_service.auth.config import ConfigAuthenticationSource
    from dump_things_service.auth.forgejo import ForgejoAuthenticationSource

    instance_config = InstanceConfig(store_path=store_path)
    instance_config.collections = config_object.collections

    for collection_name, collection_info in config_object.collections.items():
        # Create the authentication providers
        instance_config.auth_providers[collection_name] = []

        auth_provider_list = []
        # Check for multiple providers
        for auth_provider in collection_info.auth_sources:
            if auth_provider.type == 'config':
                key = ('config',)
            elif auth_provider.type == 'forgejo':
                key = (
                    'forgejo',
                    auth_provider.url,
                    auth_provider.organization,
                    auth_provider.team,
                    auth_provider.label_type,
                    auth_provider.repository,
                )
            else:
                msg = f'Unknown authentication provider type: {auth_provider.type}'
                raise ConfigError(msg)
            if key in auth_provider_list:
                logger.warning(f'Ignoring duplicate authentication provider: {key}')
                continue
            auth_provider_list.append(key)

        for auth_provider in auth_provider_list:
            if auth_provider[0] == 'config':
                instance_config.auth_providers[collection_name].append(
                    ConfigAuthenticationSource(
                        instance_config=instance_config,
                        collection=collection_name,
                    )
                )
            else:
                instance_config.auth_providers[collection_name].append(
                    ForgejoAuthenticationSource(*auth_provider[1:])
                )

        # Set the default backend if not specified
        backend = collection_info.backend or BackendConfigRecordDir(
            type='record_dir+stl'
        )

        instance_config.backend[collection_name] = backend
        backend_name, extension = get_backend_and_extension(backend.type)
        if backend_name == 'record_dir':
            # Get the config from the curated directory
            collection_config = Config.get_collection_dir_config(
                store_path / collection_info.curated
            )
            schema = collection_config.schema
        elif backend.type == 'sqlite':
            schema = backend.schema
        else:
            msg = f'Unsupported backend `{collection_info.backend}` for collection `{collection_name}`.'
            raise ConfigError(msg)

        # Generate the collection model
        model, classes, model_var_name = get_model_for_schema(schema)
        instance_config.model_info[collection_name] = model, classes, model_var_name
        globals_dict[model_var_name] = model

        # Generate the curated stores
        if backend_name == 'record_dir':
            curated_store_backend = RecordDirStore(
                root=store_path / collection_info.curated,
                pid_mapping_function=get_mapping_function(collection_config),
                suffix=collection_config.format,
                order_by=order_by,
            )
            curated_store_backend.build_index_if_needed(schema=schema)
        elif backend.type == 'sqlite':
            curated_store_backend = SQLiteBackend(
                db_path=store_path / collection_info.curated / sqlite_record_file_name,
            )
        else:
            msg = f'Unsupported backend `{collection_info.backend}` for collection `{collection_name}`.'
            raise ConfigError(msg)

        if extension == 'stl':
            curated_store_backend = SchemaTypeLayer(
                backend=curated_store_backend,
                schema=schema,
            )

        curated_store = ModelStore(
            schema=schema,
            backend=curated_store_backend,
        )

        instance_config.curated_stores[collection_name] = curated_store

        if collection_info.incoming:
            instance_config.incoming[collection_name] = collection_info.incoming

        instance_config.schemas[collection_name] = schema
        if schema not in instance_config.conversion_objects:
            instance_config.conversion_objects[schema] = get_conversion_objects(schema)

        # We do not create stores for tokens here, but leave it to the token
        # authentication routine.
        instance_config.token_stores[collection_name] = dict()

    # Read info for tokens from the configuration
    for token_name, token_info in config_object.tokens.items():
        for collection_name, token_collection_info in token_info.collections.items():

            if collection_name not in instance_config.tokens:
                instance_config.tokens[collection_name] = dict()

            permissions = get_permissions(token_collection_info.mode)
            instance_config.tokens[collection_name][token_name] = {
                'permissions': permissions,
                'user_id': token_info.user_id,
                'incoming_label': token_collection_info.incoming_label,
            }

            # There is only a token store if the token has incoming read- or
            # incoming write-permissions. If a token store exists, we ensure
            # that an incoming path is set and an incoming label exists.
            if permissions.incoming_read or permissions.incoming_write:

                # Check that the incoming label is set for a token that has
                # access rights to incoming records.
                if not token_collection_info.incoming_label:
                    msg = f'Token `{token_name}` with mode {token_collection_info.mode} must not have an empty `incoming_label`'
                    raise ConfigError(msg)

                if any(c in token_collection_info.incoming_label for c in ('\\', '/')):
                    msg = (
                        f'Incoming label for token `...` on collection '
                        f'`{collection_name}` must not contain slashes or '
                        f'backslashes: `{token_collection_info.incoming_label}`'
                    )
                    raise ConfigError(msg)

                if collection_name not in instance_config.incoming:
                    msg = (
                        'Incoming location not defined for collection '
                        f'`{collection_name}`, which has at least one token '
                        f'with write access'
                    )
                    raise ConfigError(msg)

    # Check that default tokens are defined
    for collection_name, collection_info in config_object.collections.items():
        if collection_info.default_token not in instance_config.tokens[collection_name]:
            msg = f'Unknown default token: `{collection_info.default_token}`'
            raise ConfigError(msg)

    return instance_config


def create_token_store(
    instance_config: InstanceConfig,
    collection_name: str,
    store_dir: Path,
) -> ModelStore:

    schema_uri = instance_config.schemas[collection_name]

    # We get the backend information from the curated store
    backend_type = instance_config.backend[collection_name].type
    backend_name, extension = get_backend_and_extension(backend_type)

    backend = instance_config.curated_stores[collection_name].backend
    if backend_name == 'record_dir':
        # The configuration routines have read the backend configuration of the
        # curated store from disk and stored it in `instance_config`. We fetch
        # it from there.
        if extension == 'stl':
            backend = backend.backend

        token_store = create_record_dir_token_store(
            store_dir=store_dir,
            order_by=backend.order_by,
            schema_uri=instance_config.schemas[collection_name],
            mapping_function=backend.pid_mapping_function,
            suffix=backend.suffix,
        )
    elif backend_name == 'sqlite':
        token_store = create_sqlite_token_store(
            store_dir=store_dir,
            order_by=backend.order_by,
        )
    else:
        # This should not happen because we base our decision on already
        # existing backends.
        msg = f'Unsupported backend type: `{backend_type}`.'
        raise ConfigError(msg)

    if extension == 'stl':
        token_store = SchemaTypeLayer(backend=token_store, schema=schema_uri)

    return ModelStore(backend=token_store, schema=schema_uri)


def create_record_dir_token_store(
    store_dir: Path,
    order_by: list[str],
    schema_uri: str,
    mapping_function: Callable,
    suffix: str,
) -> RecordDirStore:

    store_backend = RecordDirStore(
        root=store_dir,
        pid_mapping_function=mapping_function,
        suffix=suffix,
        order_by=order_by,
    )
    store_backend.build_index_if_needed(schema=schema_uri)
    return store_backend


def create_sqlite_token_store(
    store_dir: Path,
    order_by: list[str],
)  -> SQLiteBackend:

    return SQLiteBackend(
        db_path=store_dir / sqlite_record_file_name,
        order_by=order_by,
    )


def check_collection(
    instance_config: InstanceConfig,
    collection: str,
):
    if collection not in instance_config.collections:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f'No such collection: "{collection}".',
        )


def get_backend_and_extension(backend_type: str) -> tuple[str, str]:
    elements = backend_type.split('+')
    return (elements[0], elements[1]) if len(elements) > 1 else (elements[0], '')


def get_token_store(
    instance_config: InstanceConfig,
    collection_name: str,
    token: str
) -> tuple[ModelStore, TokenPermission] | tuple[None, None]:
    check_collection(instance_config, collection_name)

    # Check whether a store for this collection and token does already exist
    store_info = instance_config.token_stores[collection_name].get(token)
    if store_info:
        return store_info

    # Try to authenticate the token with the authentication providers that
    # are associated with the collection.
    auth_info = None
    for auth_provider in instance_config.auth_providers[collection_name]:
        try:
            auth_info = auth_provider.authenticate(token)
            break
        except AuthenticationError:
            logger.debug(
                'Authentication provider %s could not authenticate token %s.',
                auth_provider,
                token,
            )
            continue

    if not auth_info:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail='Invalid token for collection ' + collection_name,
        )

    permissions = auth_info.token_permission

    # If the token has no incoming-read or incoming-write permissions, we do not
    # need to create a store.
    if not permissions.incoming_read and not permissions.incoming_write:
        instance_config.token_stores[collection_name][token] = None
        return None, permissions

    # Check whether the collection has an incoming definition
    incoming = instance_config.incoming.get(collection_name)
    if not incoming:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail='No incoming area for collection ' +  collection_name
        )

    store_dir = instance_config.store_path / incoming / auth_info.incoming_label
    store_dir.mkdir(parents=True, exist_ok=True)

    token_store = create_token_store(
        instance_config=instance_config,
        collection_name=collection_name,
        store_dir=store_dir,
    )

    instance_config.token_stores[collection_name][token] = (
        token_store,
        permissions,
    )

    return token_store, permissions


def get_default_token_name(
    instance_config: InstanceConfig,
    collection: str
) -> str:
    check_collection(instance_config, collection)
    return instance_config.collections[collection].default_token


def join_default_token_permissions(
    instance_config: InstanceConfig,
    permissions: TokenPermission,
    collection: str,
) -> TokenPermission:
    default_token_name = instance_config.collections[collection].default_token
    default_token_permissions = instance_config.tokens[collection][default_token_name]['permissions']
    result = TokenPermission()
    result.curated_read = (
        permissions.curated_read | default_token_permissions.curated_read
    )
    result.incoming_read = (
        permissions.incoming_read | default_token_permissions.incoming_read
    )
    result.incoming_write = (
        permissions.incoming_write | default_token_permissions.incoming_write
    )
    return result


def get_zone(
    instance_config: InstanceConfig,
    collection: str,
    token: str,
) -> str | None:
    """Get the zone for the given collection and token."""
    if collection not in instance_config.zones:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f'No incoming zone defined for collection: {collection}',
        )
    if token not in instance_config.zones[collection]:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f'Missing incoming_label for given token in collection: {collection}',
        )
    return instance_config.zones[collection][token]


def get_conversion_objects_for_collection(
    instance_config: InstanceConfig,
    collection_name: str,
) -> dict:
    """Get the conversion objects for the given collection."""
    check_collection(instance_config, collection_name)
    return instance_config.conversion_objects[instance_config.schemas[collection_name]]


def get_model_info_for_collection(
    instance_config: InstanceConfig,
    collection_name: str,
) -> tuple[types.ModuleType, dict[str, Any], str]:
    check_collection(instance_config, collection_name)
    return instance_config.model_info[collection_name]
