from __future__ import annotations

import argparse
import logging
from functools import partial
from itertools import count
from pathlib import Path
from typing import (
    Annotated,  # noqa F401 -- used by generated code
    Any,
)

import uvicorn
from fastapi import (
    Body,  # noqa F401 -- used by generated code
    Depends,
    FastAPI,
    HTTPException,
)
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, TypeAdapter
from starlette.responses import (
    JSONResponse,
    PlainTextResponse,
)

from dump_things_service import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    Format,
)
from dump_things_service.config import (
    Config,
    TokenPermission,
    get_mapping_function,
    get_permissions,
)
from dump_things_service.convert import (
    convert_json_to_ttl,
    convert_ttl_to_json,
    get_conversion_objects,
)
from dump_things_service.model import (
    get_classes,
    get_model_for_schema,
    get_subclasses,
)
from dump_things_service.record import RecordDirStore
from dump_things_service.utils import (
    cleaned_json,
    combine_ttl,
)


class TokenCapabilityRequest(BaseModel):
    token: str | None


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
    'store',
    help='The root of the data stores, it should contain a global_store and token_stores.',
)

arguments = parser.parse_args()


store_path = Path(arguments.store)
if arguments.config:
    global_config = Config.get_config_from_file(Path(arguments.config))
else:
    global_config = Config.get_config(store_path)

g_curated_stores = {}
g_incoming = {}
g_zones = {}
g_model_info = {}
g_token_stores = {}
g_schemas = {}
g_conversion_objects = {}

model_var_counter = count()


# Create a model for each collection and a `RecordDirStore` for the
# `curated`-dir in each collection.
for collection_name, collection_info in global_config.collections.items():
    # Get the config from the curated directory
    config = Config.get_collection_dir_config(store_path / collection_info.curated)

    # Generate the collection model
    model, classes, model_var_name = get_model_for_schema(config.schema)
    g_model_info[collection_name] = model, classes, model_var_name
    globals()[model_var_name] = model

    curated_store = RecordDirStore(
        store_path / collection_info.curated, model, get_mapping_function(config)
    )
    g_curated_stores[collection_name] = curated_store
    if collection_info.incoming:
        g_incoming[collection_name] = collection_info.incoming

    g_schemas[collection_name] = config.schema
    if config.schema not in g_conversion_objects:
        g_conversion_objects[config.schema] = get_conversion_objects(config.schema)


# Create a `RecordDirStore` for each token dir and fetch the permissions
for token_name, token_info in global_config.tokens.items():
    entry = {'user_id': token_info.user_id, 'collections': {}}
    g_token_stores[token_name] = entry
    for collection_name, token_collection_info in token_info.collections.items():
        entry['collections'][collection_name] = {}
        # A token might be a pure curated read token, i.e., have the mode
        # `READ_COLLECTION`. In this case there will be no incoming store.
        if collection_name in g_incoming:
            if collection_name not in g_zones:
                g_zones[collection_name] = {}
            g_zones[collection_name][token_name] = token_collection_info.incoming_label
            model = g_curated_stores[collection_name].model
            mapping_function = g_curated_stores[collection_name].pid_mapping_function
            # Ensure that the store directory exists
            store_dir = (
                store_path
                / g_incoming[collection_name]
                / token_collection_info.incoming_label
            )
            store_dir.mkdir(parents=True, exist_ok=True)
            token_store = RecordDirStore(store_dir, model, mapping_function)
            entry['collections'][collection_name]['store'] = token_store
        entry['collections'][collection_name]['permissions'] = get_permissions(
            token_collection_info.mode
        )

_endpoint_template = """
async def {name}(
        data: {model_var_name}.{class_name} | Annotated[str, Body(media_type='text/plain')],
        api_key: str = Depends(api_key_header_scheme),
        format: Format = Format.json,
) -> JSONResponse | PlainTextResponse:
    lgr.info('{name}(%s, %s, %s, %s, %s)', repr(data), repr('{class_name}'), repr({model_var_name}), repr(format), repr(api_key))
    return store_record('{collection}', data, '{class_name}', {model_var_name}, format, api_key)
"""


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

    token = _get_default_token_name(collection) if api_key is None else api_key
    # Get the token permissions and extend them by the default permissions
    store, token_permissions = _get_token_store(collection, token)
    final_permissions = _join_default_token_permissions(token_permissions, collection)
    if not final_permissions.incoming_write:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f'Not authorized to submit to collection "{collection_name}".',
        )

    if input_format == Format.ttl:
        json_object = convert_ttl_to_json(collection, class_name, data)
        record = TypeAdapter(getattr(model, class_name)).validate_python(json_object)
    else:
        record = data

    stored_records = store.store_record(
        record=record,
        submitter_id=g_token_stores[token]['user_id'],
        model=model,
    )

    if input_format == Format.ttl:
        return PlainTextResponse(
            combine_ttl(
                [
                    convert_json_to_ttl(
                        collection,
                        record.__class__.__name__,
                        cleaned_json(
                            record.model_dump(mode='json', exclude_none=True),
                            remove_keys=('@type', 'schema_type'),
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
                partial(cleaned_json, remove_keys=('@type', 'schema_type')),
                map(jsonable_encoder, stored_records),
            )
        )
    )


lgr = logging.getLogger('uvicorn')

app = FastAPI()

# Add CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=arguments.origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


# Create endpoints for all classes in all collections
lgr.info('Creating dynamic endpoints...')
serial_number = count()


for collection, (model, classes, model_var_name) in g_model_info.items():
    globals()[model_var_name] = model
    for class_name in classes:
        # Create an endpoint to dump data of type `class_name` in version
        # `version` of schema `application`.
        endpoint_name = f'_endpoint_{next(serial_number)}'

        endpoint_source = _endpoint_template.format(
            name=endpoint_name,
            model_var_name=model_var_name,
            class_name=class_name,
            collection=collection,
            info=f"'store {collection}/{class_name} objects'",
        )
        exec(endpoint_source)  # noqa S102
        endpoint = locals()[endpoint_name]

        # Create an API route for the endpoint
        app.add_api_route(
            path=f'/{collection}/record/{class_name}',
            endpoint=locals()[endpoint_name],
            methods=['POST'],
            name=f'handle "{class_name}" of schema "{model.linkml_meta["id"]}" objects',
            response_model=None,
        )

lgr.info('Creation of %d endpoints completed.', next(serial_number))


@app.post('/{collection}/token_permissions')
async def fetch_token_permissions(
    collection: str,
    body: TokenCapabilityRequest,
):
    token = _get_default_token_name(collection) if body.token is None else body.token
    token_store, token_permissions = _get_token_store(collection, token)
    final_permissions = _join_default_token_permissions(token_permissions, collection)
    return JSONResponse(
        {
            'read_curated': final_permissions.curated_read,
            'read_incoming': final_permissions.incoming_read,
            'write_incoming': final_permissions.incoming_write,
            **(
                {'incoming_zone': g_zones[collection][token]}
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
    token = _get_default_token_name(collection) if api_key is None else api_key

    token_store, token_permissions = _get_token_store(collection, token)
    final_permissions = _join_default_token_permissions(token_permissions, collection)
    if not final_permissions.curated_read and not final_permissions.incoming_read:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f'No read access to curated or incoming data in collection "{collection}".',
        )

    record = None
    if final_permissions.incoming_read:
        class_name, record = token_store.get_record_by_pid(pid)

    if not record and final_permissions.curated_read:
        class_name, record = g_curated_stores[collection].get_record_by_pid(pid)

    record = cleaned_json(record, remove_keys=('@type', 'schema_type'))
    if record and format == Format.ttl:
        ttl_record = convert_json_to_ttl(collection, class_name, record)
        return PlainTextResponse(ttl_record, media_type='text/turtle')
    return record


@app.get('/{collection}/records/{class_name}')
async def read_records_of_type(
    collection: str,
    class_name: str,
    format: Format = Format.json,  # noqa A002
    api_key: str = Depends(api_key_header_scheme),
):
    token = _get_default_token_name(collection) if api_key is None else api_key

    model = g_model_info[collection][0]
    if class_name not in get_classes(model):
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f'No "{class_name}"-class in collection "{collection}".',
        )

    token_store, token_permissions = _get_token_store(collection, token)
    final_permissions = _join_default_token_permissions(token_permissions, collection)
    if not final_permissions.incoming_read and not final_permissions.curated_read:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f'No read access to curated or incoming data in collection "{collection}".',
        )

    records = {}
    if final_permissions.curated_read:
        for search_class_name in get_subclasses(model, class_name):
            for record_class_name, record in g_curated_stores[collection].get_records_of_class(
                search_class_name
            ):
                records[record['pid']] = record_class_name, record

    if final_permissions.incoming_read:
        for search_class_name in get_subclasses(model, class_name):
            for record_class_name, record in token_store.get_records_of_class(search_class_name):
                records[record['pid']] = record_class_name, record

    if format == Format.ttl:
        ttls = [
            convert_json_to_ttl(
                collection,
                target_class=record_class_name,
                json=cleaned_json(record, remove_keys=('@type', 'schema_type')),
            )
            for record_class_name, record in records.values()
        ]
        if ttls:
            return PlainTextResponse(combine_ttl(ttls), media_type='text/turtle')
        return PlainTextResponse('', media_type='text/turtle')
    return [
        cleaned_json(record, remove_keys=('@type', 'schema_type'))
        for _, record in records.values()
    ]


def _get_token_store(
    collection_name: str, token: str
) -> tuple[RecordDirStore, TokenPermission] | tuple[None, None]:
    if collection_name not in g_curated_stores:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f'No such collection: "{collection_name}".',
        )
    if token not in g_token_stores:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail='Invalid token.')

    token_store = None
    permissions = g_token_stores[token]['collections'][collection_name]['permissions']
    if permissions.incoming_write or permissions.incoming_read:
        token_store = g_token_stores[token]['collections'][collection_name]['store']
    return token_store, permissions


def _get_default_token_name(collection: str) -> str:
    try:
        return global_config.collections[collection].default_token
    except KeyError as e:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail=f'No such collection: {collection}'
        ) from e


def _join_default_token_permissions(
    permissions: TokenPermission,
    collection: str,
) -> TokenPermission:
    default_token_name = global_config.collections[collection].default_token
    default_token_permissions = g_token_stores[default_token_name]['collections'][collection]['permissions']
    result = TokenPermission()
    result.curated_read = permissions.curated_read | default_token_permissions.curated_read
    result.incoming_read = permissions.incoming_read | default_token_permissions.incoming_read
    result.incoming_write = permissions.incoming_write | default_token_permissions.incoming_write
    return result


# Rebuild the app to include all dynamically created endpoints
app.openapi_schema = None
app.setup()


if __name__ == '__main__':
    uvicorn.run(
        app,
        host=arguments.host,
        port=arguments.port,
        root_path=arguments.root_path,
    )
