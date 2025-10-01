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
    cleaned_json,
    resolve_hashed_token,
    wrap_http_exception,
)

if TYPE_CHECKING:
    from dump_things_service.lazy_list import LazyList

_endpoint_curated_template = """
async def {name}(
    data: {model_var_name}.{class_name},
    api_key: str = Depends(api_key_header_scheme),
) -> JSONResponse:
    logger.info(
        '{name}(%s, %s)',
        repr(data),
        repr({model_var_name}),
    )
    return await store_curated_record(
        '{collection}',
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
    '/{collection}/curated/records/{class_name}',
    tags=['Curator read records'],
)
async def read_curated_records_of_type(
    collection: str,
    class_name: str,
    matching: str | None = None,
    api_key: str | None = Depends(api_key_header_scheme),
):
    return await _read_curated_records(
        collection=collection,
        class_name=class_name,
        pid=None,
        matching=matching,
        api_key=api_key,
        upper_bound=500,
    )


@router.get(
    '/{collection}/curated/records/p/{class_name}',
    tags=['Curator read records'],
)
async def read_curated_records_of_type_paginated(
    collection: str,
    class_name: str,
    matching: str | None = None,
    api_key: str | None = Depends(api_key_header_scheme),
) -> Page[dict]:
    record_list = await _read_curated_records(
        collection=collection,
        class_name=class_name,
        pid=None,
        matching=matching,
        api_key=api_key,
    )
    return paginate(record_list)


@router.get(
    '/{collection}/curated/records/',
    tags=['Curator read records'],
)
async def read_curated_all_records(
    collection: str,
    matching: str | None = None,
    api_key: str | None = Depends(api_key_header_scheme),
):
    return await _read_curated_records(
        collection=collection,
        class_name=None,
        pid=None,
        matching=matching,
        api_key=api_key,
        upper_bound=500,
    )


@router.get(
    '/{collection}/curated/records/p/',
    tags=['Curator read records'],
)
async def read_curated_all_records_paginated(
    collection: str,
    matching: str | None = None,
    api_key: str | None = Depends(api_key_header_scheme),
) -> Page[dict]:
    record_list = await _read_curated_records(
        collection=collection,
        class_name=None,
        pid=None,
        matching=matching,
        api_key=api_key,
    )
    return paginate(record_list)


@router.get(
    '/{collection}/curated/record',
    tags=['Curator read records'],
)
async def read_curated_record_with_pid(
    collection: str,
    pid: str,
    api_key: str = Depends(api_key_header_scheme),
):
    return await _read_curated_records(
        collection=collection,
        class_name=None,
        pid=pid,
        api_key=api_key,
    )


@router.delete(
    '/{collection}/curated/record',
    tags=['Curator delete records'],
)
async def delete_curated_record_with_pid(
    collection: str,
    pid: str,
    api_key: str = Depends(api_key_header_scheme),
):
    return await _delete_curated_record(
        collection=collection,
        pid=pid,
        api_key=api_key,
    )


async def _read_curated_records(
    collection: str,
    class_name: str | None,
    pid: str | None,
    matching: str | None = None,
    api_key: str | None = None,
    upper_bound: int = 1000,
) -> LazyList | dict | None:

    model_store, backend = await _get_store_and_backend(collection, api_key)

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
            f'/curated/records/p/{class_name}',
        )

    return ModifierList(
        result_list,
        lambda record_info: record_info.json_object,
    )


async def _delete_curated_record(
        collection: str,
        pid: str | None,
        api_key: str | None = None,
) -> bool:
    model_store, backend = await _get_store_and_backend(collection, api_key)
    return backend.remove_record(model_store.pid_to_iri(pid))


async def _get_store_and_backend(
    collection: str,
    api_key: str | None,
) -> tuple[ModelStore, StorageBackend]:

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

    # A curator token can only come from the configuration
    if hashed_token not in instance_config.tokens[collection]:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail='ConfigAuthenticationSource: token not valid for collection '
                   f'`{collection}`',
        )

    permissions = instance_config.tokens[collection][hashed_token]['permissions']
    if permissions.curated_write is False:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=f'no write access to curated area of collection `{collection}`',
        )

    # Get the curated model store
    model_store = instance_config.curated_stores[collection]
    backend = model_store.backend
    if isinstance(backend, _SchemaTypeLayer):
        return model_store, backend.backend
    return model_store, backend


def create_curated_endpoints(
    app: FastAPI,
    global_dict: dict,
):
    # Create endpoints for all classes in all collections
    logger.info('Creating dynamic curated endpoints...')
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
            # `application`.
            endpoint_name = f'_endpoint_curated_{next(serial_number)}'

            endpoint_source = _endpoint_curated_template.format(
                name=endpoint_name,
                model_var_name=model_var_name,
                class_name=class_name,
                collection=collection,
                info=f"'store {collection}/{class_name} objects'",
            )
            exec(endpoint_source, global_dict)  # noqa S102

            # Create an API route for the endpoint
            app.add_api_route(
                path=f'/{collection}/curated/record/{class_name}',
                endpoint=global_dict[endpoint_name],
                methods=['POST'],
                name=f'curated store of "{class_name}" object (schema: {model.linkml_meta["id"]})',
                response_model=None,
                tags=[f'Curator write records to "{collection}"']
            )

    logger.info(
        'Creation of %d curated endpoints completed.',
        next(serial_number),
    )


async def store_curated_record(
    collection: str,
    data: BaseModel,
    class_name: str,
    api_key: str | None = Depends(api_key_header_scheme),
):

    pid = data.pid
    model_store, backend = await _get_store_and_backend(collection, api_key)

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
