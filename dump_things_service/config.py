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
    ConfigDict,
    Field,
    ValidationError,
)
from yaml.scanner import ScannerError

from dump_things_service import HTTP_404_NOT_FOUND
from dump_things_service.backends.record_dir import RecordDirStore
from dump_things_service.backends.schema_type_layer import SchemaTypeLayer
from dump_things_service.backends.sqlite import SQLiteBackend
from dump_things_service.backends.sqlite import (
    record_file_name as sqlite_record_file_name,
)
from dump_things_service.converter import get_conversion_objects
from dump_things_service.exceptions import (
    ConfigError,
    CurieResolutionError,
)
from dump_things_service.model import get_model_for_schema
from dump_things_service.resolve_curie import resolve_curie
from dump_things_service.store.model_store import ModelStore
from dump_things_service.token import (
    TokenPermission,
    get_token_parts,
    hash_token,
)
from dump_things_service.utils import check_collection

if TYPE_CHECKING:
    import types

logger = logging.getLogger('dump_things_service')

config_file_name = '.dumpthings.yaml'
ignored_files = {'.', '..', config_file_name}


_global_config_instance = None


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class MappingMethod(enum.Enum):
    digest_md5 = 'digest-md5'
    digest_md5_p3 = 'digest-md5-p3'
    digest_md5_p3_p3 = 'digest-md5-p3-p3'
    digest_sha1 = 'digest-sha1'
    digest_sha1_p3 = 'digest-sha1-p3'
    digest_sha1_p3_p3 = 'digest-sha1-p3-p3'
    after_last_colon = 'after-last-colon'


class CollectionDirConfig(StrictModel):
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
    CURATOR = 'CURATOR'


class TokenCollectionConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    mode: TokenModes
    incoming_label: str = Field(strict=True)


class TokenConfig(StrictModel):
    user_id: str
    collections: dict[str, TokenCollectionConfig]
    hashed: bool = False


class BackendConfigRecordDir(StrictModel):
    type: Literal['record_dir', 'record_dir+stl']


class BackendConfigSQLite(StrictModel):
    type: Literal['sqlite', 'sqlite+stl']
    schema: str


class ForgejoAuthConfig(StrictModel):
    type: Literal['forgejo']
    url: str
    organization: str
    team: str
    label_type: Literal['team', 'user']
    repository: str | None = None


class ConfigAuthConfig(StrictModel):
    type: Literal['config'] = 'config'


class TagConfig(StrictModel):
    submitter_id_tag: str = 'http://purl.obolibrary.org/obo/NCIT_C54269'
    submission_time_tag: str = 'http://semanticscience.org/resource/SIO_001083'


class CollectionConfig(StrictModel):
    default_token: str
    curated: Path
    incoming: Path | None = None
    backend: BackendConfigRecordDir | BackendConfigSQLite | None = None
    auth_sources: list[ForgejoAuthConfig | ConfigAuthConfig] = [ConfigAuthConfig()]
    submission_tags: TagConfig = TagConfig()


class GlobalConfig(StrictModel):
    model_config = ConfigDict(strict=True)

    type: Literal['collections']
    version: Literal[1]
    collections: dict[str, CollectionConfig]
    tokens: dict[str, TokenConfig]


@dataclasses.dataclass
class InstanceConfig:
    store_path: Path
    collections: dict = dataclasses.field(default_factory=dict)
    all_stores: dict = dataclasses.field(default_factory=dict)
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
    hashed_tokens: dict = dataclasses.field(default_factory=dict)


mode_mapping = {
    TokenModes.READ_CURATED: TokenPermission(curated_read=True),
    TokenModes.READ_COLLECTION: TokenPermission(
        curated_read=True,
        incoming_read=True,
    ),
    TokenModes.WRITE_COLLECTION: TokenPermission(
        curated_read=True,
        incoming_read=True,
        incoming_write=True,
    ),
    TokenModes.READ_SUBMISSIONS: TokenPermission(incoming_read=True),
    TokenModes.WRITE_SUBMISSIONS: TokenPermission(
        incoming_read=True,
        incoming_write=True,
    ),
    TokenModes.SUBMIT: TokenPermission(curated_read=True, incoming_write=True),
    TokenModes.SUBMIT_ONLY: TokenPermission(incoming_write=True),
    TokenModes.NOTHING: TokenPermission(),
    TokenModes.CURATOR: TokenPermission(
        curated_read=True,
        incoming_read=True,
        incoming_write=True,
        curated_write=True,
        zones_access=True,
    ),
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
    global global_config_instance

    config_object = Config.get_config_from_file(config_file)
    global_config_instance = process_config_object(
        store_path=store_path,
        config_object=config_object,
        order_by=order_by,
        globals_dict=globals_dict,
    )


def get_config():
    return global_config_instance


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
            tags={
                'id': collection_info.submission_tags.submitter_id_tag,
                'time': collection_info.submission_tags.submission_time_tag,
            }
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

            if collection_name not in instance_config.hashed_tokens:
                instance_config.hashed_tokens[collection_name] = dict()

            if token_info.hashed:
                token_id, _ = get_token_parts(token_name)
                if token_id == '':
                    raise ConfigError('empty ID in hashed token')
                if token_id in instance_config.hashed_tokens[collection_name]:
                    msg = f'duplicated ID in hashed token: {token_id}'
                    raise ConfigError(msg)
                instance_config.hashed_tokens[collection_name][token_id] = token_name

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

                # Create all incoming zones
                incoming_location = (
                    store_path
                    / instance_config.collections[collection_name].incoming
                    / token_collection_info.incoming_label
                )
                incoming_location.mkdir(parents=True, exist_ok=True)

    # Check that default tokens are defined
    for collection_name, collection_info in config_object.collections.items():
        if collection_info.default_token not in instance_config.tokens[collection_name]:
            msg = f'Unknown default token: `{collection_info.default_token}`'
            raise ConfigError(msg)

    # Check that hashed plain tokens do not clash with hashed tokens:
    hashed_plain_tokens = set(
        hash_token(token)
        for collection in instance_config.collections
        for token in instance_config.tokens[collection]
        if '-' in token
    )
    hashed_tokens = set(
        value
        for token_dict in instance_config.hashed_tokens.values()
        for value in token_dict.values()
    )
    if hashed_plain_tokens.intersection(hashed_tokens):
        msg = 'plain tokens clash with hashed tokens'
        raise ConfigError(msg)

    # Check tags
    for collection_name, collection_info in config_object.collections.items():
        module = instance_config.model_info[collection_name][0]
        try:
            resolve_curie(module, collection_info.submission_tags.submission_time_tag)
        except CurieResolutionError as e:
            raise ConfigError(str(e)) from e

    return instance_config


def get_backend_and_extension(backend_type: str) -> tuple[str, str]:
    elements = backend_type.split('+')
    return (elements[0], elements[1]) if len(elements) > 1 else (elements[0], '')


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
