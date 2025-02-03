from __future__ import annotations

import argparse
import logging
from http.client import HTTPException
from itertools import count
from pathlib import Path
from typing import (
    Annotated,
    Any,
)

import uvicorn
from fastapi import (
    FastAPI,
    Form,
    Header,
    HTTPException,
)
from pydantic import BaseModel

from .model import build_model, get_classes
from .storage import Storage


parser = argparse.ArgumentParser()
parser.add_argument('--host', default='0.0.0.0')
parser.add_argument('--port', default=8000, type=int)
parser.add_argument('store', help='The root of the data stores, it should contain a global_store and token_stores.')

arguments = parser.parse_args()


# Instantiate storage objects
store = Path(arguments.store)
global_store = Storage(store / 'global_store')
token_stores = {
    element.name : Storage(Path(element))
    for element in (store / 'token_stores').glob('*')
    if element.is_dir()
}


_endpoint_template = """
async def {name}(
        data: Annotated[{model_var_name}.{type}, Form(), {info}],
        x_dumpthings_token: Annotated[str | None, Header()]
):
    lgr.info('{name}(%s, %s)', repr(data.model_dump()), repr(x_dumpthings_token))
    return store_record('{label}', data, x_dumpthings_token)
"""


def store_record(
    label: str,
    data: BaseModel,
    token: str | None,
) -> Any:
    if token is None:
        raise HTTPException(status_code=401, detail='Token missing.')
    _get_store_for_token(token).store_record(record=data, label=label)
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


# Create endpoints for all applications, all versions, and all classes
lgr.info('Creating dynamic endpoints...')
serial_number = count()


for label, (model, classes, model_var_name) in model_info.items():
    for type_name in classes:
        # Create an endpoint to dump data of type `type_name` in version
        # `version` of schema `application`.
        endpoint_name = f'_endpoint_{next(serial_number)}'
        exec(_endpoint_template.format(
            name=endpoint_name,
            model_var_name=model_var_name,
            type=type_name,
            label=label,
            info=f"'endpoint for {label}/{type_name}'"
        ))
        endpoint = locals()[endpoint_name]

        # Create an API route for the endpoint
        app.add_api_route(
            path=f'/{label}/record/{type_name}',
            endpoint=locals()[endpoint_name],
            methods=['POST'],
            name=f'handle "{type_name}" of schema "{model.linkml_meta["id"]}" objects',
            response_model=getattr(model, type_name)
        )

lgr.info('Creation of %d endpoints completed.', next(serial_number))


@app.get('/{label}/record/{identifier}')
async def read_item(
    label: str,
    identifier: str,
    x_dumpthings_token: Annotated[str | None, Header()] = None
):
    store = _get_store_for_token(x_dumpthings_token)
    if store:
        record = store.get_record(label, identifier)
        if record:
            return record
    return global_store.get_record(label, identifier)


@app.get('/{label}/records/{type_name}')
def read_item(
    label: str,
    type_name: str,
    x_dumpthings_token: Annotated[str | None, Header()] = None
):
    records = {}
    store = _get_store_for_token(x_dumpthings_token)
    if store:
        for record in store.get_all_records(label, type_name):
            records[record['id']] = record
    for record in global_store.get_all_records(label, type_name):
        records[record['id']] = record
    yield from records.values()


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
        if element.is_dir and element.name not in token_stores:
            token_stores[element.name] = Storage(Path(element))
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
