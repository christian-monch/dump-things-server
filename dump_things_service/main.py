from __future__ import annotations   # noqa: I001 -- the patches have to be imported early

import argparse
import logging
import sys
from functools import partial
from pathlib import Path
from typing import (
    Annotated,  # noqa F401 -- used by generated code
    Any,
)

# Perform the patching before importing any third-party libraries
from dump_things_service.patches import enabled  # noqa: F401

import uvicorn
from fastapi import (
    Body,  # noqa F401 -- used by generated code
    Depends,
    FastAPI,
    HTTPException,
    Request,
)
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import (
    BaseModel,
    TypeAdapter,
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
from dump_things_service.config import (
    ConfigError,
    InstanceConfig,
    get_default_token_name,
    get_model_info_for_collection,
    get_token_store,
    get_zone,
    join_default_token_permissions,
    process_config,
)
from dump_things_service.convert import (
    convert_json_to_ttl,
    convert_ttl_to_json,
)
from dump_things_service.dynamic_endpoints import create_endpoints
from dump_things_service.model import (
    get_classes,
    get_subclasses,
)
from dump_things_service.resolve_curie import resolve_curie
from dump_things_service.utils import (
    cleaned_json,
    combine_ttl,
)


class TokenCapabilityRequest(BaseModel):
    token: str | None


logger = logging.getLogger('dump_things_service')
uvicorn_logger = logging.getLogger('uvicorn')


parser = argparse.ArgumentParser()
parser.add_argument('--host', default='0.0.0.0')  # noqa S104
parser.add_argument('--port', default=8000, type=int)
parser.add_argument('--origins', action='append', default=[])
parser.add_argument('-c', '--config')
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
    'store',
    help='The root of the data stores, it should contain a global_store and token_stores.',
)


arguments = parser.parse_args()

# Set the log level
numeric_level = getattr(logging, arguments.log_level.upper(), None)
if not isinstance(numeric_level, int):
    logger.error('Invalid log level: %s, defaulting to level "WARNING"', arguments.log_level)
else:
    logging.basicConfig(level=numeric_level)

store_path = Path(arguments.store)

g_error = None

config_path = Path(arguments.config) if arguments.config else store_path / config_file_name
try:
    g_instance_config = process_config(
        store_path=store_path,
        config_file=config_path,
        globals_dict=globals(),
    )
except ConfigError:
    logger.exception(
        'ERROR: invalid configuration file at: `%s`',
        config_path,
    )
    g_error = 'Server runs in error mode due to an invalid configuration. See server error-log for details.'


app = FastAPI()


def handle_global_error():
    if g_error:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=g_error)


# If a global error exists, it does not make sense to activate the defined
# endpoints because we don't have a working configuration. Instead, we signal
# the error to any request that is made to the server.
if g_error:
    if __name__ == '__main__' and arguments.error_mode:
        logger.warning('Server runs in error mode, all endpoints will return error information.')

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


api_key_header_scheme = APIKeyHeader(
    name='X-DumpThings-Token',
    # authentication is generally optional
    auto_error=False,
    scheme_name='submission',
    description='Presenting a valid token enables record submission, and retrieval of records submitted with this token prior curation.',
)


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

    _check_collection(g_instance_config, collection)

    token = get_default_token_name(g_instance_config, collection) if api_key is None else api_key
    # Get the token permissions and extend them by the default permissions
    store, token_permissions = get_token_store(g_instance_config, collection, token)
    final_permissions = join_default_token_permissions(g_instance_config, token_permissions, collection)
    if not final_permissions.incoming_write:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f'Not authorized to submit to collection "{collection}".',
        )

    if input_format == Format.ttl:
        json_object = convert_ttl_to_json(
            g_instance_config,
            collection,
            class_name,
            data,
        )
        record = TypeAdapter(getattr(model, class_name)).validate_python(json_object)
    else:
        record = data

    stored_records = tuple(
        store.store_record(
            record=record,
            submitter_id=g_instance_config.token_stores[token]['user_id'],
            model=model,
        )
    )

    # Add `schema_type` to the records
    for record in stored_records:
        record.schema_type = _get_schema_type_curie(
            collection,
            record.__class__.__name__,
        )

    if input_format == Format.ttl:
        return PlainTextResponse(
            combine_ttl(
                [
                    convert_json_to_ttl(
                        g_instance_config,
                        collection,
                        record.__class__.__name__,
                        cleaned_json(
                            record.model_dump(mode='json', exclude_none=True),
                            remove_keys=('@type',),
                        )
                    )
                    for record in stored_records
                ]
            ),
            media_type='text/turtle',
        )
    return JSONResponse(
        list(
            map(
                partial(cleaned_json),
                map(jsonable_encoder, stored_records),
            )
        )
    )


def _check_collection(
    instance_config: InstanceConfig,
    collection: str,
):
    if collection not in instance_config.collections:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f'No such collection: "{collection}".',
        )


# Add CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=arguments.origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.post('/{collection}/token_permissions')
async def fetch_token_permissions(
    collection: str,
    body: TokenCapabilityRequest,
):
    _check_collection(g_instance_config, collection)
    token = get_default_token_name(g_instance_config, collection) if body.token is None else body.token
    token_store, token_permissions = get_token_store(g_instance_config, collection, token)
    final_permissions = join_default_token_permissions(g_instance_config, token_permissions, collection)
    return JSONResponse(
        {
            'read_curated': final_permissions.curated_read,
            'read_incoming': final_permissions.incoming_read,
            'write_incoming': final_permissions.incoming_write,
            **(
                {'incoming_zone': get_zone(g_instance_config, collection, token)}
                if final_permissions.incoming_read or final_permissions.incoming_write
                else {}
            ),
        }
    )


@app.get('/{collection}/record')
async def read_record_with_pid(
    collection: str,
    pid: str,
    format: Format = Format.json,  # noqa A002
    api_key: str = Depends(api_key_header_scheme),
):
    _check_collection(g_instance_config, collection)

    token = get_default_token_name(g_instance_config, collection) if api_key is None else api_key

    token_store, token_permissions = get_token_store(g_instance_config, collection, token)
    final_permissions = join_default_token_permissions(g_instance_config, token_permissions, collection)
    if not final_permissions.curated_read and not final_permissions.incoming_read:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f'No read access to curated or incoming data in collection "{collection}".',
        )

    iri = resolve_curie(
        get_model_info_for_collection(g_instance_config, collection)[0],
        pid,
    )
    record = None
    if final_permissions.incoming_read:
        class_name, record = token_store.get_record_by_iri(iri)

    if not record and final_permissions.curated_read:
        class_name, record = g_instance_config.curated_stores[collection].get_record_by_iri(iri)

    if record:
        if format == Format.ttl:
            ttl_record = convert_json_to_ttl(
                g_instance_config,
                collection,
                class_name,
                record,
            )
            return PlainTextResponse(ttl_record, media_type='text/turtle')
        record['schema_type'] = _get_schema_type_curie(collection, class_name)
    return record


@app.get('/{collection}/records/{class_name}')
async def read_records_of_type(
    collection: str,
    class_name: str,
    format: Format = Format.json,  # noqa A002
    api_key: str = Depends(api_key_header_scheme),
):
    _check_collection(g_instance_config, collection)

    token = get_default_token_name(g_instance_config, collection) if api_key is None else api_key

    model = g_instance_config.model_info[collection][0]
    if class_name not in get_classes(model):
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f'No "{class_name}"-class in collection "{collection}".',
        )

    token_store, token_permissions = get_token_store(g_instance_config, collection, token)
    final_permissions = join_default_token_permissions(g_instance_config, token_permissions, collection)
    if not final_permissions.incoming_read and not final_permissions.curated_read:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f'No read access to curated or incoming data in collection "{collection}".',
        )

    records = {}
    if final_permissions.curated_read:
        for search_class_name in get_subclasses(model, class_name):
            for record_class_name, record in g_instance_config.curated_stores[collection].get_records_of_class(
                search_class_name
            ):
                record['schema_type'] = _get_schema_type_curie(collection, record_class_name)
                records[record['pid']] = record

    if final_permissions.incoming_read:
        for search_class_name in get_subclasses(model, class_name):
            for record_class_name, record in token_store.get_records_of_class(search_class_name):
                record['schema_type'] = _get_schema_type_curie(collection, record_class_name)
                records[record['pid']] = record

    if format == Format.ttl:
        ttls = [
            convert_json_to_ttl(
                g_instance_config,
                collection,
                target_class=record_class_name,
                json=cleaned_json(record),
            )
            for record in records.values()
        ]
        if ttls:
            return PlainTextResponse(combine_ttl(ttls), media_type='text/turtle')
        return PlainTextResponse('', media_type='text/turtle')
    return tuple(records.values())


def _get_schema_type_curie(
    collection: str,
    class_name: str,
) -> str:
    schema_url = g_instance_config.schemas[collection]
    schema_module = g_instance_config.conversion_objects[schema_url]['schema_module']
    class_object = getattr(schema_module, class_name)
    return class_object.class_class_curie


# Create dynamic endpoints and rebuild the app to include all dynamically
# created endpoints.
create_endpoints(app, g_instance_config, globals())
app.openapi_schema = None
app.setup()


def main():
    uvicorn.run(
        app,
        host=arguments.host,
        port=arguments.port,
        root_path=arguments.root_path,
    )


if __name__ == '__main__':
    main()
