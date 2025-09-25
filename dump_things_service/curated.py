from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi_pagination import (
    Page,
    add_pagination,
    paginate,
)

from dump_things_service import (
    HTTP_401_UNAUTHORIZED,
    HTTP_413_REQUEST_ENTITY_TOO_LARGE,
)
from dump_things_service.api_key import api_key_header_scheme
from dump_things_service.backends.schema_type_layer import _SchemaTypeLayer
from dump_things_service.config import get_config
from dump_things_service.lazy_list import ModifierList
from dump_things_service.utils import (
    check_collection,
    resolve_hashed_token,

)

if TYPE_CHECKING:
    from dump_things_service.lazy_list import LazyList

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


@router.get('/{collection}/curated/records/{class_name}')
async def read_curated_records_of_type(
    collection: str,
    class_name: str,
    matching: str | None = None,
    api_key: str | None = Depends(api_key_header_scheme),
):
    return await _read_curated_records(
        collection,
        class_name,
        matching,
        api_key,
        500,
    )


@router.get('/{collection}/curated/records/p/{class_name}')
async def read_curated_records_of_type_paginated(
    collection: str,
    class_name: str,
    matching: str | None = None,
    api_key: str | None = Depends(api_key_header_scheme),
) -> Page[dict]:
    record_list = await _read_curated_records(
        collection,
        class_name,
        matching,
        api_key,
        500,
    )
    return paginate(record_list)


@router.get('/{collection}/curated/records/')
async def read_curated_all_records(
        collection: str,
        matching: str | None = None,
        api_key: str | None = Depends(api_key_header_scheme),
):
    return await _read_curated_records(
        collection,
        None,
        matching,
        api_key,
        500,
    )


@router.get('/{collection}/curated/records/p/')
async def read_curated_all_records_paginated(
        collection: str,
        matching: str | None = None,
        api_key: str | None = Depends(api_key_header_scheme),
) -> Page[dict]:
    record_list = await _read_curated_records(
        collection,
        None,
        matching,
        api_key,
        500,
    )
    return paginate(record_list)


async def _read_curated_records(
    collection: str,
    class_name: str | None,
    matching: str | None = None,
    api_key: str | None = None,
    upper_bound: int = 1000,
) -> LazyList:
    # This can only be used with a token
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
    backend = instance_config.curated_stores[collection].backend
    if isinstance(backend, _SchemaTypeLayer):
        backend = backend.backend

    if class_name:
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
