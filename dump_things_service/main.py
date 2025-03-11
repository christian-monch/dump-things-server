from __future__ import annotations

import argparse
import json
import logging
from itertools import count
from pathlib import Path
from typing import (
    TYPE_CHECKING,
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
from starlette.responses import (
    JSONResponse,
    PlainTextResponse,
)

from dump_things_service import Format
from dump_things_service.model import (
    build_model,
    get_classes,
    get_subclasses,
)
from dump_things_service.storage import (
    Storage,
    TokenStorage,
)
from dump_things_service.utils import (
    cleaned_json,
    combine_ttl,
)

if TYPE_CHECKING:
    from pydantic import BaseModel


parser = argparse.ArgumentParser()
parser.add_argument('--host', default='0.0.0.0')  # noqa S104
parser.add_argument('--port', default=8000, type=int)
parser.add_argument('--origins', action='append', default=[])
parser.add_argument(
    'store',
    help='The root of the data stores, it should contain a global_store and token_stores.',
)

arguments = parser.parse_args()


# Instantiate storage objects
store = Path(arguments.store)
global_store = Storage(store / 'global_store')
token_stores = {
    element.name: TokenStorage(element, global_store)
    for element in (store / 'token_stores').glob('*')
    if element.is_dir()
}


_endpoint_template = """
async def {name}(
        data: {model_var_name}.{class_name} | Annotated[str, Body(media_type='text/plain')],
        api_key: str = Depends(api_key_header_scheme),
        format: Format = Format.json,
) -> JSONResponse | PlainTextResponse:
    lgr.info('{name}(%s, %s, %s, %s, %s)', repr(data), repr('{class_name}'), repr({model_var_name}), repr(format), repr(api_key))
    return store_record('{collection}', data, '{class_name}', {model_var_name}, format, api_key)
"""


def store_record(
    collection: str,
    data: BaseModel | str,
    class_name: str,
    model: Any,
    input_format: Format,
    token: str | None,
) -> JSONResponse | PlainTextResponse:
    if input_format == Format.json and isinstance(data, str):
        raise HTTPException(status_code=404, detail='Invalid JSON data provided.')

    if input_format == Format.ttl and not isinstance(data, str):
        raise HTTPException(status_code=404, detail='Invalid ttl data provided.')

    store = _get_store_for_token(token)
    if store:
        stored_records = store.store_record(
            record=data,
            collection=collection,
            model=model,
            class_name=class_name,
            input_format=input_format,
        )
        if input_format == Format.ttl:
            return PlainTextResponse(data, media_type='text/turtle')
        return JSONResponse(
            list(map(cleaned_json, map(jsonable_encoder, stored_records)))
        )
    raise HTTPException(status_code=403, detail='Invalid token.')


lgr = logging.getLogger('uvicorn')


# Create pydantic models from schema sources and add them to globals
model_info = {}
model_counter = count()
created_models = {}
for collection, configuration in global_store.collections.items():
    schema_location = configuration.schema
    if schema_location not in created_models:
        lgr.info(
            f'Building model for collection {collection} from schema {schema_location}.'
        )
        model = build_model(schema_location)
        classes = get_classes(model)
        model_var_name = f'model_{next(model_counter)}'
        created_models[schema_location] = model, classes, model_var_name
        globals()[model_var_name] = model
    else:
        lgr.info(
            f'Using existing model for collection {collection} from schema {schema_location}.'
        )
    model_info[collection] = created_models[schema_location]


app = FastAPI()
api_key_header_scheme = APIKeyHeader(
    name='X-DumpThings-Token',
    # authentication is generally optional
    auto_error=False,
    scheme_name='submission',
    description='Presenting a valid token enables record submission, and retrieval of records submitted with this token prior curation.',
)

# Add CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=arguments.origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Create endpoints for all applications, all versions, and all classes
lgr.info('Creating dynamic endpoints...')
serial_number = count()


for collection, (model, classes, model_var_name) in model_info.items():
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


@app.get('/{collection}/record')
async def read_record_with_id(
    collection: str,
    id: str,  # noqa A002
    format: Format = Format.json,  # noqa A002
    api_key: str = Depends(api_key_header_scheme),
):
    identifier = id
    store = _get_store_for_token(api_key)
    record = None
    if store:
        record = store.get_record(collection, identifier, format)
    if not record:
        record = global_store.get_record(collection, identifier, format)

    if record:
        if format == Format.ttl:
            return PlainTextResponse(record, media_type='text/turtle')
        return record
    return None


@app.get('/{collection}/records/{class_name}')
async def read_records_of_type(
    collection: str,
    class_name: str,
    format: Format = Format.json,  # noqa A002
    api_key: str = Depends(api_key_header_scheme),
):
    from dump_things_service.convert import convert_format

    if collection not in model_info:
        raise HTTPException(
            status_code=401, detail=f'No such collection: "{collection}".'
        )

    model = model_info[collection][0]
    if class_name not in get_classes(model):
        raise HTTPException(
            status_code=401, detail=f'Unsupported class: "{class_name}".'
        )

    records = {}
    for search_class_name in get_subclasses(model, class_name):
        for record in global_store.get_all_records(collection, search_class_name):
            records[record['id']] = record
    store = _get_store_for_token(api_key)
    if store:
        for search_class_name in get_subclasses(model, class_name):
            for record in store.get_all_records(collection, search_class_name):
                records[record['id']] = record

    if format == Format.ttl:
        ttls = [
            convert_format(
                target_class=class_name,
                data=json.dumps(record),
                input_format=Format.json,
                output_format=format,
                **(global_store.conversion_objects[collection]),
            )
            for record in records.values()
        ]
        if ttls:
            return PlainTextResponse(combine_ttl(ttls), media_type='text/turtle')
        return PlainTextResponse('', media_type='text/turtle')
    return list(records.values())


def _get_store_for_token(token: str | None):
    if token is None:
        return None
    if token not in token_stores:
        _update_token_stores(store, token_stores)
    if token not in token_stores:
        raise HTTPException(status_code=401, detail='Invalid token.')
    return token_stores[token]


def _update_token_stores(
    store: Path,
    token_stores: dict,
) -> int:
    added = 0
    for element in (store / 'token_stores').glob('*'):
        if element.is_dir() and element.name not in token_stores:
            token_stores[element.name] = TokenStorage(element, global_store)
            added += 1
    return added


# Rebuild the app to include all dynamically created endpoints
app.openapi_schema = None
app.setup()


if __name__ == '__main__':
    uvicorn.run(
        app,
        host=arguments.host,
        port=arguments.port,
    )
