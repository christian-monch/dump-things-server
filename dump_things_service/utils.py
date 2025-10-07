from __future__ import annotations

import logging
import sys
from contextlib import contextmanager
from functools import reduce
from typing import (
    TYPE_CHECKING,
    Callable,
)

import fsspec
from fastapi import HTTPException
from rdflib import Graph
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from dump_things_service import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from dump_things_service.auth import AuthenticationError
from dump_things_service.token import (
    TokenPermission,
    get_token_parts,
)

if TYPE_CHECKING:
    from pathlib import Path

    from dump_things_service import JSON
    from dump_things_service.backends.record_dir import RecordDirStore
    from dump_things_service.backends.sqlite import SQLiteBackend
    from dump_things_service.config import InstanceConfig
    from dump_things_service.store.model_store import ModelStore


logger = logging.getLogger('dump_things_service')


@contextmanager
def sys_path(paths: list[str | Path]):
    """Patch the `Path` class to return the paths in `paths` in order."""
    original_path = sys.path
    try:
        sys.path = [str(path) for path in paths]
        yield
    finally:
        sys.path = original_path


def read_url(url: str) -> str:
    """
    Read the content of an URL into memory.
    """
    open_file = fsspec.open(url, 'rt')
    with open_file as f:
        return f.read()


def cleaned_json(data: JSON, remove_keys: tuple[str, ...] = ('@type',)) -> JSON:
    if isinstance(data, list):
        return [cleaned_json(item, remove_keys) for item in data]
    if isinstance(data, dict):
        return {
            key: cleaned_json(value, remove_keys)
            for key, value in data.items()
            if key not in remove_keys and data[key] is not None
        }
    return data


def combine_ttl(documents: list[str]) -> str:
    graphs = [Graph().parse(data=doc, format='ttl') for doc in documents]
    return reduce(lambda g1, g2: g1 + g2, graphs).serialize(format='ttl')


def get_schema_type_curie(
    instance_config: InstanceConfig,
    collection: str,
    class_name: str,
) -> str:
    schema_url = instance_config.schemas[collection]
    schema_module = instance_config.conversion_objects[schema_url]['schema_module']
    class_object = getattr(schema_module, class_name)
    return class_object.class_class_curie


@contextmanager
def wrap_http_exception(
    exception_class: type[BaseException] = ValueError,
    status_code: int = HTTP_400_BAD_REQUEST,
    header: str = ''
):
    """Wrap exceptions of class `exception_class` into HTTP exceptions"""
    try:
        yield
    except exception_class as e:
        raise HTTPException(
            status_code=status_code,
            detail=f'{header}: {e}' if header else str(e),
        )


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


def check_collection(
    instance_config: InstanceConfig,
    collection: str,
):
    if collection not in instance_config.collections:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f'No such collection: "{collection}".',
        )


def check_label(
    instance_config: InstanceConfig,
    collection: str,
    label: str,
):
    # Get the on-disk labels for the collection
    if (
            label not in get_config_labels(instance_config, collection)
            and label not in get_on_disk_labels(instance_config, collection)
    ):
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f'No incoming label: "{label}" in collection: "{collection}".',
        )


def get_config_labels(
    instance_config: InstanceConfig,
    collection: str,
) -> set[str]:
    check_collection(instance_config, collection)
    return {
        token['incoming_label']
        for token in instance_config.tokens[collection].values()
        if token['incoming_label'] != ''
    }


def get_on_disk_labels(
    instance_config: InstanceConfig,
    collection: str,
) -> set[str]:
    check_collection(instance_config, collection)

    incoming_path = instance_config.collections[collection].incoming
    if not incoming_path or not incoming_path.exists():
        return set()

    return {
        path.name
        for path in incoming_path.iterdir()
        if path.is_dir()
    }


def get_default_token_name(
    instance_config: InstanceConfig,
    collection: str
) -> str:
    check_collection(instance_config, collection)
    return instance_config.collections[collection].default_token


async def process_token(
    instance_config: InstanceConfig,
    api_key: str,
    collection: str,
) -> tuple[TokenPermission, ModelStore]:
    token = (
        get_default_token_name(instance_config, collection)
        if api_key is None
        else api_key
    )

    token_store, token, token_permissions, _ = get_token_store(
        instance_config,
        collection,
        token,
    )
    final_permissions = join_default_token_permissions(
        instance_config, token_permissions, collection
    )
    if not final_permissions.incoming_read and not final_permissions.curated_read:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f'No read access to curated or incoming data in collection "{collection}".',
        )
    return final_permissions, token_store


def resolve_hashed_token(
        instance_config: InstanceConfig,
        collection_name: str,
        token: str,
) -> str:

    # Check for hashed token and return the hashed token value instead
    # of the plain text token value if the token is hashed.
    if '-' in token:
        return instance_config.hashed_tokens[collection_name].get(
            get_token_parts(token)[0],
            token,
        )
    return token


def get_token_store(
        instance_config: InstanceConfig,
        collection_name: str,
        plain_token: str
) -> tuple[ModelStore, str, TokenPermission, str] | tuple[None, None, None, None]:
    check_collection(instance_config, collection_name)

    # If the token is hashed, get the hashed value. This is required because
    # we associate token info with the hashed version of the token.
    hashed_token = resolve_hashed_token(
        instance_config,
        collection_name,
        plain_token,
    )

    # Check whether a store for this collection and token does already exist.
    # If the token is a hashed token, we have to
    store_info = instance_config.token_stores[collection_name].get(plain_token)
    if store_info:
        return store_info

    # Try to authenticate the token with the authentication providers that
    # are associated with the collection.
    auth_info = None
    messages = []
    for auth_provider in instance_config.auth_providers[collection_name]:
        try:
            logger.debug('trying to authenticate with %s', auth_provider)
            auth_info = auth_provider.authenticate(plain_token)
            break
        except AuthenticationError as ae:
            logger.debug(
                'Authentication provider %s could not '
                'authenticate token for collection %s: %s',
                auth_provider,
                collection_name,
                str(ae),
            )
            messages.append(f'{auth_provider.__class__.__name__} failed with: {ae}')
            continue

    if not auth_info:
        detail = f'invalid token for collection {collection_name}: ' + ', '.join(
            messages,
        )
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=detail,
        )

    permissions = auth_info.token_permission

    # If the token has no incoming-read or incoming-write permissions, we do not
    # need to create a store.
    if not permissions.incoming_read and not permissions.incoming_write:
        instance_config.token_stores[collection_name][plain_token] = (
            None,
            hashed_token,
            permissions,
            auth_info.user_id,
        )
        return instance_config.token_stores[collection_name][plain_token]

    # Check whether the collection has an incoming definition
    incoming = instance_config.incoming.get(collection_name)
    if not incoming:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail='No incoming area for collection ' +  collection_name
        )

    store_dir = instance_config.store_path / incoming / auth_info.incoming_label
    token_store = create_token_store(
        instance_config=instance_config,
        collection_name=collection_name,
        store_dir=store_dir,
    )

    instance_config.token_stores[collection_name][plain_token] = (
        token_store,
        hashed_token,
        permissions,
        auth_info.user_id,
    )
    return instance_config.token_stores[collection_name][plain_token]


def create_token_store(
        instance_config: InstanceConfig,
        collection_name: str,
        store_dir: Path,
) -> ModelStore:
    from dump_things_service.backends.schema_type_layer import SchemaTypeLayer
    from dump_things_service.config import (
        ConfigError,
        get_backend_and_extension,
    )
    from dump_things_service.store.model_store import ModelStore

    # Check if the store was already created and if it was created for the
    # same schema.
    if store_dir in instance_config.all_stores:
        existing_collection_name, existing_model_store = instance_config.all_stores[store_dir]
        if (
            existing_collection_name != collection_name
            and instance_config.schemas[existing_collection_name] != instance_config.schemas[collection_name]
        ):
            msg = (
                f'collections "{existing_collection_name}" and {collection_name}"'
                f' with different schemas map onto the same storage directory: '
                f'"<incoming_path>/{store_dir.name}"'
            )
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=msg,
            )
        return existing_model_store

    store_dir.mkdir(parents=True, exist_ok=True)

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

    submission_tags = instance_config.collections[collection_name].submission_tags
    tags = {
        'id': submission_tags.submitter_id_tag,
        'time': submission_tags.submission_time_tag,
    }
    model_store = ModelStore(backend=token_store, schema=schema_uri, tags=tags)
    instance_config.all_stores[store_dir] = (collection_name, model_store)

    return model_store


def create_record_dir_token_store(
        store_dir: Path,
        order_by: list[str],
        schema_uri: str,
        mapping_function: Callable,
        suffix: str,
) -> RecordDirStore:
    from dump_things_service.backends.record_dir import RecordDirStore

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
    from dump_things_service.backends.sqlite import SQLiteBackend
    from dump_things_service.backends.sqlite import (
        record_file_name as sqlite_record_file_name,
    )

    return SQLiteBackend(
        db_path=store_dir / sqlite_record_file_name,
        order_by=order_by,
    )
