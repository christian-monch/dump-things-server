from __future__ import annotations

import argparse
import logging
import json
from http.client import HTTPException
from itertools import count
from pathlib import Path
from typing import (
    Annotated,
    Any,
)

import uvicorn
from fastapi import (
    Body,
    FastAPI,
    Header,
    HTTPException,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.responses import PlainTextResponse

from . import Format
from .model import build_model, get_classes
from .storage import (
    Storage,
    TokenStorage,
)
from .utils import combine_ttl


parser = argparse.ArgumentParser()
parser.add_argument('--host', default='0.0.0.0')
parser.add_argument('--port', default=8000, type=int)
parser.add_argument('--origins', action='append', default=[])
parser.add_argument('store', help='The root of the data stores, it should contain a global_store and token_stores.')

arguments = parser.parse_args()


# Instantiate storage objects
store = Path(arguments.store)
global_store = Storage(store / 'global_store')
token_stores = {
    element.name : TokenStorage(element, global_store)
    for element in (store / 'token_stores').glob('*')
    if element.is_dir()
}


_endpoint_template = """
async def {name}(
        data: {model_var_name}.{class_name} | Annotated[str, Body(media_type='text/plain')],
        x_dumpthings_token: Annotated[str | None, Header()],
        format: Format = Format.json,
):
    lgr.info('{name}(%s, %s, %s, %s)', repr(data), repr('{class_name}'), repr(format), repr(x_dumpthings_token))
    return store_record('{label}', data, '{class_name}', format, x_dumpthings_token)
"""


def store_record(
    label: str,
    data: BaseModel | str,
    class_name: str,
    format: Format,
    token: str | None,
) -> Any:
    if format == Format.json and isinstance(data, str):
        raise HTTPException(status_code=404, detail="Invalid JSON data provided.")

    _get_store_for_token(token).store_record(
        record=data,
        label=label,
        class_name=class_name,
        format=format,
    )
    if format == Format.ttl:
        return PlainTextResponse(data, media_type='text/turtle')
    else:
        return data


lgr = logging.getLogger('uvicorn')


# Create pydantic models from schema sources and add them to globals
model_info = {}
model_counter = count()
for label, configuration in global_store.collections.items():
    schema_location = configuration.schema
    lgr.info(f'Building model for {label} from {schema_location}.')
    model = build_model(schema_location)
    classes = get_classes(model)
    model_var_name = f'model_{next(model_counter)}'
    model_info[label] = model, classes, model_var_name
    globals()[model_var_name] = model


app = FastAPI()
# Add CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=arguments.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create endpoints for all applications, all versions, and all classes
lgr.info('Creating dynamic endpoints...')
serial_number = count()


for label, (model, classes, model_var_name) in model_info.items():
    for class_name in classes:
        # Create an endpoint to dump data of type `class_name` in version
        # `version` of schema `application`.
        endpoint_name = f'_endpoint_{next(serial_number)}'

        endpoint_source = _endpoint_template.format(
            name=endpoint_name,
            model_var_name=model_var_name,
            class_name=class_name,
            label=label,
            info=f"'store {label}/{class_name} objects'"
        )
        exec(endpoint_source)
        endpoint = locals()[endpoint_name]

        # Create an API route for the endpoint
        app.add_api_route(
            path=f'/{label}/record/{class_name}',
            endpoint=locals()[endpoint_name],
            methods=['POST'],
            name=f'handle "{class_name}" of schema "{model.linkml_meta["id"]}" objects',
            response_model=getattr(model, class_name)
        )

lgr.info('Creation of %d endpoints completed.', next(serial_number))


@app.get('/{label}/record')
async def read_record_with_id(
    label: str,
    id: str,
    format: Format = Format.json,
    x_dumpthings_token: Annotated[str | None, Header()] = None
):
    identifier = id
    store = _get_store_for_token(x_dumpthings_token)
    record = None
    if store:
        record = store.get_record(label, identifier, format)
    if not record:
        record = global_store.get_record(label, identifier, format)

    if record:
        if format == Format.ttl:
            return PlainTextResponse(record, media_type='text/turtle')
        else:
            return record


@app.get('/{label}/records/{class_name}')
async def read_records_of_type(
    label: str,
    class_name: str,
    format: Format = Format.json,
    x_dumpthings_token: Annotated[str | None, Header()] = None
):
    from .convert import convert_format

    records = {}
    for record in global_store.get_all_records(label, class_name):
        records[record['id']] = record
    store = _get_store_for_token(x_dumpthings_token)
    if store:
        for record in store.get_all_records(label, class_name):
            records[record['id']] = record

    if format == Format.ttl:
        ttls = [
            convert_format(
                target_class=class_name,
                data=json.dumps(record),
                input_format=Format.json,
                output_format=format,
                **(global_store.conversion_objects[label])
            )
            for record in records.values()
        ]
        if ttls:
            return PlainTextResponse(combine_ttl(ttls), media_type='text/turtle')
        return PlainTextResponse('', media_type='text/turtle')
    else:
        return list(records.values())


def _get_store_for_token(token: str|None):
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
