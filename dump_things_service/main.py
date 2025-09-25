from __future__ import annotations  # noqa: I001 -- the patches have to be imported early

import argparse
import logging
import sys
from pathlib import Path
from typing import (
    Annotated,  # noqa F401 -- used by generated code
    Any,
    TYPE_CHECKING,
)

from starlette.status import HTTP_413_REQUEST_ENTITY_TOO_LARGE

# Perform the patching before importing any third-party libraries
from dump_things_service.patches import enabled  # noqa: F401

import uvicorn
from fastapi import (
    Body,  # noqa F401 -- used by generated code
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,  # noqa F401 -- used by generated code
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import (
    Page,
    add_pagination,
    paginate,
)
from fastapi_pagination.utils import disable_installed_extensions_check
from pydantic import (
    BaseModel,
    TypeAdapter,
    ValidationError,
)
from starlette.responses import (
    JSONResponse,
    PlainTextResponse,
)

from dump_things_service import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    Format,
    config_file_name,
)
from dump_things_service.__about__ import __version__
from dump_things_service.api_key import api_key_header_scheme
from dump_things_service.config import (
    ConfigError,
    get_config,
    process_config,
)
from dump_things_service.converter import (
    FormatConverter,
    ConvertingList,
)
from dump_things_service.curated import (
    create_curated_endpoints,
    router as curated_router,
    store_curated_record,  # noqa F401 -- used by generated code
)
from dump_things_service.incoming import (
    create_incoming_endpoints,
    router as incoming_router,
    store_incoming_record,  # noqa F401 -- used by generated code
)
from dump_things_service.dynamic_endpoints import create_endpoints
from dump_things_service.export import exporter_info
from dump_things_service.lazy_list import (
    PriorityList,
    ModifierList,
)
from dump_things_service.model import (
    get_classes,
    get_subclasses,
)
from dump_things_service.utils import (
    check_collection,
    combine_ttl,
    get_default_token_name,
    get_token_store,
    join_default_token_permissions,
    process_token,
    wrap_http_exception,
)

if TYPE_CHECKING:
    from dump_things_service.lazy_list import LazyList


class TokenCapabilityRequest(BaseModel):
    token: str | None


class ServerResponse(BaseModel):
    version: str


logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger('dump_things_service')


parser = argparse.ArgumentParser()
parser.add_argument('--host', default='0.0.0.0')  # noqa S104
parser.add_argument('--port', default=8000, type=int)
parser.add_argument('--origins', action='append', default=[])
parser.add_argument(
    '-c',
    '--config',
    metavar='CONFIG_FILE',
    help="Read the configuration from 'CONFIG_FILE' instead of looking for it in the data store root directory. ",
)
parser.add_argument(
    '--root-path',
    default='',
    help="Set the ASGI 'root_path' for applications submounted below a given URL path.",
)
parser.add_argument(
    '--error-mode',
    action='store_true',
    help="Don't exit with non-zero status on errors that prevent the service from proper operation, instead return the error on every request.",
)
parser.add_argument(
    '--log-level',
    default='WARNING',
    help="Set the log level for the service, allowed values are 'ERROR', 'WARNING', 'INFO', 'DEBUG'. Default is 'warning'.",
)
parser.add_argument(
    '--export-json',
    default='',
    metavar='FILE_NAME',
    help="Export the store to the file FILE_NAME and exit the process. If FILE_NAME is `-', the data is written to stdout.",
)
parser.add_argument(
    '--export-tree',
    default='',
    metavar='DIRECTORY_NAME',
    help='Export the store to a dumpthings-conformant tree at DIRECTORY_NAME and exit the process. If DIRECTORY_NAME does not exist, the service will try to create it.',
)
parser.add_argument(
    'store',
    help='The root of the data stores, it should contain a global_store and token_stores.',
)


arguments = parser.parse_args()

# Set the log level
numeric_level = getattr(logging, arguments.log_level.upper(), None)
if not isinstance(numeric_level, int):
    logger.error(
        'Invalid log level: %s, defaulting to level "WARNING"', arguments.log_level
    )
else:
    logger.setLevel(level=numeric_level)

store_path = Path(arguments.store)

g_error = None

config_path = (
    Path(arguments.config) if arguments.config else store_path / config_file_name
)

g_instance_config = None
try:
    process_config(
        store_path=store_path,
        config_file=config_path,
        order_by=['pid'],
        globals_dict=globals(),
    )
    g_instance_config = get_config()
except ConfigError as e:
    logger.error(
        'ERROR: invalid configuration `%s`: %s',
        config_path,
        e,
    )
    g_error = 'Server runs in error mode due to an invalid configuration. See server error-log for details.'


for switch in ('json', 'tree'):
    argument = getattr(arguments, 'export_' + switch)
    if argument:
        if g_error:
            sys.stderr.write(
                'ERROR: Configuration errors detected, cannot export store.'
            )
            sys.exit(1)
        exporter_info[switch](g_instance_config, argument)
        sys.exit(0)


disable_installed_extensions_check()

app = FastAPI()
app.include_router(curated_router)
app.include_router(incoming_router)

def handle_global_error():
    if g_error:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=g_error)


# If a global error exists, it does not make sense to activate the defined
# endpoints because we don't have a working configuration. Instead, we signal
# the error to any request that is made to the server.
if g_error:
    if __name__ == '__main__' and arguments.error_mode:
        logger.warning(
            'Server runs in error mode, all endpoints will return error information.'
        )

        @app.post('/{full_path:path}')
        def post_global_error(request: Request, full_path: str):  # noqa: ARG001
            handle_global_error()

        @app.get('/{full_path:path}')
        def get_global_error(request: Request, full_path: str):  # noqa: ARG001
            handle_global_error()

        uvicorn.run(
            app,
            host=arguments.host,
            port=arguments.port,
            root_path=arguments.root_path,
        )
    sys.exit(1)


def store_record(
    collection: str,
    data: BaseModel | str,
    class_name: str,
    model: Any,
    input_format: Format,
    api_key: str | None = Depends(api_key_header_scheme),
) -> JSONResponse | PlainTextResponse:
    if input_format == Format.json and isinstance(data, str):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail='Invalid JSON data provided.'
        )

    if input_format == Format.ttl and not isinstance(data, str):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail='Invalid ttl data provided.'
        )

    check_collection(g_instance_config, collection)

    token = (
        get_default_token_name(g_instance_config, collection)
        if api_key is None
        else api_key
    )

    # Get the token permissions and extend them by the default permissions.
    # This call will also convert plaintext tokens into the hashed version of
    # the token, if the token is hashed. This is necessary because we do not
    # store the plaintext token, so all token-information is associated with
    # the hashed representation of the token.
    store, token, token_permissions, user_id = get_token_store(
        g_instance_config,
        collection,
        token,
    )
    final_permissions = join_default_token_permissions(
        g_instance_config, token_permissions, collection
    )
    if not final_permissions.incoming_write:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f'Not authorized to submit to collection "{collection}".',
        )

    if input_format == Format.ttl:
        with wrap_http_exception(ValueError, header='Conversion error'):
            json_object = FormatConverter(
                g_instance_config.schemas[collection],
                input_format=Format.ttl,
                output_format=Format.json,
            ).convert(data, class_name)
        with wrap_http_exception(ValidationError, header='Validation error'):
            record = TypeAdapter(getattr(model, class_name)).validate_python(json_object)
    else:
        record = data

    stored_records = store.store_object(obj=record, submitter=user_id)

    if input_format == Format.ttl:
        format_converter = FormatConverter(
            g_instance_config.schemas[collection],
            input_format=Format.json,
            output_format=Format.ttl,
        )
        with wrap_http_exception(ValueError, header='Conversion error'):
            return PlainTextResponse(
                combine_ttl(
                    [
                        format_converter.convert(
                            record,
                            class_name,
                        )
                        for class_name, record in stored_records
                    ]
                ),
                media_type='text/turtle',
            )
    return JSONResponse([record for _, record in stored_records])


@app.get('/server', tags=['Server'])
async def get_server() -> ServerResponse:
    return ServerResponse(
        version = __version__,
    )


@app.get('/{collection}/record', tags=['Read records'])
async def read_record_with_pid(
    collection: str,
    pid: str,
    format: Format = Format.json,  # noqa A002
    api_key: str = Depends(api_key_header_scheme),
):
    check_collection(g_instance_config, collection)

    final_permissions, token_store = await process_token(
        g_instance_config, api_key, collection
    )

    class_name, json_object = None, None
    if final_permissions.incoming_read:
        class_name, json_object = token_store.get_object_by_pid(pid)

    if not json_object and final_permissions.curated_read:
        class_name, json_object = g_instance_config.curated_stores[
            collection
        ].get_object_by_pid(pid)

    if not json_object:
        return None

    if format == Format.ttl:
        converter = FormatConverter(
            schema=g_instance_config.schemas[collection],
            input_format=Format.json,
            output_format=format,
        )
        with wrap_http_exception(ValueError, header='Conversion error'):
            ttl_record = converter.convert(json_object, class_name)
        return PlainTextResponse(ttl_record, media_type='text/turtle')
    return json_object


@app.get('/{collection}/records/', tags=['Read records'])
async def read_all_records(
        collection: str,
        matching: str | None = None,
        format: Format = Format.json,  # noqa A002
        api_key: str = Depends(api_key_header_scheme),
):
    return await _read_all_records(
        collection=collection,
        matching=matching,
        format=format,
        api_key=api_key,
        # Set an upper limit for the number of non-paginated result records to
        # keep processing time for individual requests short and avoid
        # overloading the server.
        bound=1000,
    )


@app.get('/{collection}/records/p/', tags=['Read records'])
async def read_all_records(
        collection: str,
        matching: str | None = None,
        format: Format = Format.json,  # noqa A002
        api_key: str = Depends(api_key_header_scheme),
) -> Page[dict | str]:
    result_list = await _read_all_records(
        collection=collection,
        matching=matching,
        format=format,
        api_key=api_key,
        bound=None,
    )
    return paginate(result_list)


@app.get('/{collection}/records/{class_name}', tags=['Read records'])
async def read_records_of_type(
    collection: str,
    class_name: str,
    matching: str | None = None,
    format: Format = Format.json,  # noqa A002
    api_key: str = Depends(api_key_header_scheme),
):
    return await _read_records_of_type(
        collection=collection,
        class_name=class_name,
        matching=matching,
        format=format,
        api_key=api_key,
        # Set an upper limit for the number of non-paginated result records to
        # keep processing time for individual requests short and avoid
        # overloading the server.
        bound=1000,
    )


@app.get('/{collection}/records/p/{class_name}', tags=['Read records'])
async def read_records_of_type_paginated(
    collection: str,
    class_name: str,
    matching: str | None = None,
    format: Format = Format.json,  # noqa A002
    api_key: str = Depends(api_key_header_scheme),
) -> Page[dict | str]:
    result_list = await _read_records_of_type(
        collection=collection,
        class_name=class_name,
        matching=matching,
        format=format,
        api_key=api_key,
        bound=None,
    )
    return paginate(result_list)


async def _read_all_records(
        collection: str,
        matching: str | None = None,
        format: Format = Format.json,  # noqa A002
        api_key: str = Depends(api_key_header_scheme),
        bound: int | None = None,
) -> LazyList:
    def check_bounds(length: int, max_length: int):
        if length > max_length:
            raise HTTPException(
                status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f'Too many records found in collection "{collection}". '
                       f'Please use pagination (/{collection}/records/p/).',
            )

    def convert_to_http_exception(e: BaseException):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f'Conversion error: {e}',
        ) from e

    check_collection(g_instance_config, collection)
    final_permissions, token_store = await process_token(
        g_instance_config, api_key, collection
    )

    result_list = PriorityList()
    if final_permissions.incoming_read:
        token_store_list = token_store.get_all_objects(matching=matching)
        if bound:
            check_bounds(len(token_store_list), bound)
        result_list.add_list(token_store_list)

    if final_permissions.curated_read:
        curated_store_list = g_instance_config.curated_stores[
            collection
        ].get_all_objects(
            matching=matching,
        )
        if bound:
            check_bounds(len(curated_store_list), bound)
        result_list.add_list(curated_store_list)

    # Sort the result list.
    result_list.sort(key=result_list.sort_key)

    if format == Format.ttl:
        result_list = ConvertingList(
            result_list,
            g_instance_config.schemas[collection],
            input_format=Format.json,
            output_format=format,
            exception_handler=convert_to_http_exception,
        )
    else:
        result_list = ModifierList(
            result_list,
            lambda record_info: record_info.json_object,
        )
    return result_list


async def _read_records_of_type(
    collection: str,
    class_name: str,
    matching: str | None = None,
    format: Format = Format.json,  # noqa A002
    api_key: str = Depends(api_key_header_scheme),
    bound: int | None = None,
) -> LazyList:
    def check_bounds(length: int, max_length: int):
        if length > max_length:
            raise HTTPException(
                status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f'Too many records found for class "{class_name}" in '
                f'collection "{collection}". Please use pagination '
                f'(/{collection}/records/p/{class_name}).',
            )

    def convert_to_http_exception(e: BaseException):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f'Conversion error: {e}',
        ) from e

    check_collection(g_instance_config, collection)
    model = g_instance_config.model_info[collection][0]
    if class_name not in get_classes(model):
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f'No "{class_name}"-class in collection "{collection}".',
        )

    final_permissions, token_store = await process_token(
        g_instance_config, api_key, collection
    )

    result_list = PriorityList()
    if final_permissions.incoming_read:
        for search_class_name in get_subclasses(model, class_name):
            token_store_list = token_store.get_objects_of_class(
                class_name=search_class_name,
                matching=matching,
            )
            if bound:
                check_bounds(len(token_store_list), bound)
            result_list.add_list(token_store_list)

    if final_permissions.curated_read:
        for search_class_name in get_subclasses(model, class_name):
            curated_store_list = g_instance_config.curated_stores[
                collection
            ].get_objects_of_class(
                class_name=search_class_name,
                matching=matching,
            )
            if bound:
                check_bounds(len(curated_store_list), bound)
            result_list.add_list(curated_store_list)

    # Sort the result list.
    result_list.sort(key=result_list.sort_key)

    if format == Format.ttl:
        result_list = ConvertingList(
            result_list,
            g_instance_config.schemas[collection],
            input_format=Format.json,
            output_format=format,
            exception_handler=convert_to_http_exception,
        )
    else:
        result_list = ModifierList(
            result_list,
            lambda record_info: record_info.json_object,
        )
    return result_list


@app.get('/{collection}/delete', tags=['Delete records'])
async def delete_record(
    collection: str,
    pid: str,
    api_key: str = Depends(api_key_header_scheme),
):
    check_collection(g_instance_config, collection)
    final_permissions, token_store = await process_token(
        g_instance_config, api_key, collection
    )

    if not final_permissions.incoming_write:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f'No write access to incoming data in collection "{collection}".',
        )

    return token_store.delete_object(pid)


# If we have a valid configuration, create dynamic endpoints and rebuild the
# app to include all dynamically created endpoints.
if g_instance_config:
    create_endpoints(app, g_instance_config, globals())
    create_curated_endpoints(app, globals())
    create_incoming_endpoints(app, globals())
    app.openapi_schema = None
    app.setup()

# Add CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=arguments.origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Add pagination
add_pagination(app)


def main():
    uvicorn.run(
        app,
        host=arguments.host,
        port=arguments.port,
        root_path=arguments.root_path,
    )


if __name__ == '__main__':
    main()
