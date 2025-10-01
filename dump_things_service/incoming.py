from __future__ import annotations

import logging
from itertools import count
from typing import TYPE_CHECKING

from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    HTTPException,
)
from fastapi_pagination import (
    Page,
    add_pagination,
    paginate,
)
from pydantic import BaseModel

from dump_things_service import (
    HTTP_401_UNAUTHORIZED,
    HTTP_413_REQUEST_ENTITY_TOO_LARGE,
)
from dump_things_service.api_key import api_key_header_scheme
from dump_things_service.backends import StorageBackend
from dump_things_service.backends.schema_type_layer import _SchemaTypeLayer
from dump_things_service.config import get_config
from dump_things_service.exceptions import CurieResolutionError
from dump_things_service.lazy_list import ModifierList
from dump_things_service.store.model_store import ModelStore
from dump_things_service.utils import (
    check_collection,
    check_label,
    cleaned_json,
    create_token_store,
    get_config_labels,
    get_on_disk_labels,
    resolve_hashed_token, wrap_http_exception,
)

if TYPE_CHECKING:
    from dump_things_service.lazy_list import LazyList

_endpoint_incoming_template = """
async def {name}(
    data: {model_var_name}.{class_name},
    label: str,
    api_key: str = Depends(api_key_header_scheme),
) -> JSONResponse:
    logger.info(
        '{name}(%s, %s, %s)',
        repr(data),
        repr(label),
        repr({model_var_name}),
    )
    return await store_incoming_record(
        '{collection}',
        label,
        data,
        '{class_name}',
        api_key,
    )
"""


logger = logging.getLogger('dump_things_service')
router = APIRouter()
add_pagination(router)


def check_bounds(
        length: int | None,
        max_length: int,
        collection: str,
        alternative_url: str
):
    if length > max_length:
        raise HTTPException(
            status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f'Too many records found in collection "{collection}". '
                   f'Please use pagination (/{collection}{alternative_url}).',
        )


@router.get(
    '/{collection}/incoming/',
    tags=['Incoming read labels'],
)
async def incoming_read_labels(
    collection: str,
    api_key: str | None = Depends(api_key_header_scheme),
) -> list[str]:
    # Authorize api_key
    await authorize_zones(collection, api_key)
    configured_labels = get_config_labels(get_config(), collection)
    on_disk_labels = get_on_disk_labels(get_config(), collection)
    return list(configured_labels.union(on_disk_labels))


@router.get(
    '/{collection}/incoming/{label}/records/{class_name}',
    tags=['Incoming read records'],
)
async def incoming_read_records_of_type(
    collection: str,
    label: str,
    class_name: str,
    matching: str | None = None,
    api_key: str | None = Depends(api_key_header_scheme),
):
    return await _incoming_read_records(
        collection=collection,
        label=label,
        class_name=class_name,
        pid=None,
        matching=matching,
        api_key=api_key,
        upper_bound=500,
    )


@router.get(
    '/{collection}/incoming/{label}/records/p/{class_name}',
    tags=['Incoming read records'],
)
async def incoming_read_records_of_type_paginated(
    collection: str,
    label: str,
    class_name: str,
    matching: str | None = None,
    api_key: str | None = Depends(api_key_header_scheme),
) -> Page[dict]:
    record_list = await _incoming_read_records(
        collection=collection,
        label=label,
        class_name=class_name,
        pid=None,
        matching=matching,
        api_key=api_key,
    )
    return paginate(record_list)


@router.get(
    '/{collection}/incoming/{label}/records/',
    tags=['Incoming read records'],
)
async def incoming_read_all_records(
    collection: str,
    label: str,
    matching: str | None = None,
    api_key: str | None = Depends(api_key_header_scheme),
):
    return await _incoming_read_records(
        collection=collection,
        label=label,
        class_name=None,
        pid=None,
        matching=matching,
        api_key=api_key,
        upper_bound=500,
    )


@router.get(
    '/{collection}/incoming/{label}/records/p/',
    tags=['Incoming read records'],
)
async def incoming_read_all_records_paginated(
        collection: str,
        label: str,
        matching: str | None = None,
        api_key: str | None = Depends(api_key_header_scheme),
) -> Page[dict]:
    record_list = await _incoming_read_records(
        collection=collection,
        label=label,
        class_name=None,
        pid=None,
        matching=matching,
        api_key=api_key,
    )
    return paginate(record_list)


@router.get(
    '/{collection}/incoming/{label}/record',
    tags=['Incoming read records'],
)
async def incoming_read_record_with_pid(
        collection: str,
        label: str,
        pid: str,
        api_key: str = Depends(api_key_header_scheme),
):
    return await _incoming_read_records(
        collection=collection,
        label=label,
        class_name=None,
        pid=pid,
        api_key=api_key,
    )


@router.delete(
    '/{collection}/incoming/{label}/record',
    tags=['Incoming delete records'],
)
async def incoming_delete_record_with_pid(
    collection: str,
    label: str,
    pid: str,
    api_key: str = Depends(api_key_header_scheme),
):
    return await _incoming_delete_record(
        collection=collection,
        label=label,
        pid=pid,
        api_key=api_key,
    )


async def _incoming_read_records(
        collection: str,
        label: str,
        class_name: str | None,
        pid: str | None,
        matching: str | None = None,
        api_key: str | None = None,
        upper_bound: int = 1000,
) -> LazyList | dict | None:

    model_store, backend = await _get_store_and_backend(collection, label, api_key)

    if pid:
        return backend.get_record_by_iri(model_store.pid_to_iri(pid))
    elif class_name:
        result_list = backend.get_records_of_classes([class_name], matching)
    else:
        result_list = backend.get_all_records(matching)

    if upper_bound is not None:
        check_bounds(
            len(result_list),
            upper_bound,
            collection,
            f'/incoming/records/p/{class_name}',
        )

    return ModifierList(
        result_list,
        lambda record_info: record_info.json_object,
    )


async def _incoming_delete_record(
    collection: str,
    label: str,
    pid: str | None,
    api_key: str | None = None,
) -> bool:
    model_store, backend = await _get_store_and_backend(collection, label, api_key)
    return backend.remove_record(model_store.pid_to_iri(pid))


async def _get_store_and_backend(
    collection: str,
    label: str,
    plain_token: str | None,
) -> tuple[ModelStore, StorageBackend]:

    # Authorize api_key
    await authorize_zones(collection, plain_token)

    # Check that the incoming zone exists
    instance_config = get_config()
    check_label(instance_config, collection, label)

    # Create a store (or get an already created store) for collection
    # `collection` and storage dir `store_dir`.
    store_dir = (
            instance_config.store_path
            / instance_config.incoming[collection]
            / label
    )
    # `create_token_store` will cache and return already created stores with
    # the same collection and storage dir.
    model_store = create_token_store(
        instance_config=instance_config,
        collection_name=collection,
        store_dir=store_dir,
    )

    # For consistency, associate the store with all matching tokens from the
    # configuration file.
    matching_tokens = [
        token
        for token, token_info in instance_config.tokens[collection].items()
        if token_info['incoming_label'] == label
    ]
    for matching_token in matching_tokens:
        # Associate the store with all matching tokens in the configuration.
        # Note: there are stores that are not associated with a token in
        # the configuration. These are stores that belong to a token that
        # are authenticated with an external authentication source.
        token_info = instance_config.tokens[collection][matching_token]
        instance_config.token_stores[collection][matching_token] = (
            model_store,
            matching_token,
            token_info['permissions'],
            token_info['user_id'],
        )

    backend = model_store.backend
    if isinstance(backend, _SchemaTypeLayer):
        return model_store, backend.backend
    return model_store, backend


async def authorize_zones(
    collection: str,
    api_key: str | None,
):
    # A token is required
    if api_key is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail='token required',
        )

    instance_config = get_config()

    # Check that the collection exists
    check_collection(instance_config, collection)

    # Get token permissions
    # If the token is hashed, get the hashed value. This is required because
    # we associate token info with the hashed version of the token.
    hashed_token = resolve_hashed_token(
        instance_config,
        collection,
        api_key,
    )

    # A token with zone access can only come from the configuration
    if hashed_token not in instance_config.tokens[collection]:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail='ConfigAuthenticationSource: token not valid for collection '
                   f'`{collection}`',
        )

    permissions = instance_config.tokens[collection][hashed_token]['permissions']
    if permissions.zones_access is False:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=f'no access to incoming zones of collection `{collection}`',
        )


def create_incoming_endpoints(
    app: FastAPI,
    global_dict: dict,
):
    # Create endpoints for all classes in all collections
    logger.info('Creating dynamic incoming endpoints...')
    serial_number = count()

    instance_config = get_config()

    for collection, (
            model,
            classes,
            model_var_name,
    ) in instance_config.model_info.items():

        if model_var_name not in global_dict:
            global_dict[model_var_name] = model

        for class_name in classes:
            # Create an endpoint to dump data of type `class_name` of schema
            # `model`.
            endpoint_name = f'_endpoint_incoming_{next(serial_number)}'

            endpoint_source = _endpoint_incoming_template.format(
                name=endpoint_name,
                model_var_name=model_var_name,
                class_name=class_name,
                collection=collection,
                info=f"'store {collection}/{class_name} objects'",
            )
            exec(endpoint_source, global_dict)  # noqa S102

            # Create an API route for the endpoint
            app.add_api_route(
                path=f'/{collection}/incoming/{{label}}/record/{class_name}',
                endpoint=global_dict[endpoint_name],
                methods=['POST'],
                name=f'incoming store for "{class_name}" object (schema: {model.linkml_meta["id"]})',
                response_model=None,
                tags=[f'Incoming write records to "{collection}"']
            )

    logger.info(
        'Creation of %d incoming endpoints completed.',
        next(serial_number),
    )


async def store_incoming_record(
        collection: str,
        label: str,
        data: BaseModel,
        class_name: str,
        api_key: str | None = Depends(api_key_header_scheme),
):

    pid = data.pid
    model_store, backend = await _get_store_and_backend(
        collection,
        label,
        api_key,
    )

    json_object = cleaned_json(
        data.model_dump(exclude_none=True, mode='json'),
        remove_keys=('@type',),
    )

    with wrap_http_exception(CurieResolutionError):
        backend.add_record(
            model_store.pid_to_iri(pid),
            class_name,
            json_object,
        )
