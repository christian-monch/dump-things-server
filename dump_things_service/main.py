from __future__ import annotations

import logging
import os
from itertools import count
from typing import (
    Annotated,
    Any,
)

import yaml
from fastapi import (
    FastAPI,
    Form,
    Header,
)
from pydantic import BaseModel

from dump_things_service.model import build_model, get_classes
from dump_things_service.storage import Storage


# load config
config_file = os.environ.get('DUMPTHINGS_CONFIG_FILE', './dumpthings_conf.yaml')
with open(config_file, 'rt') as f:
    config = yaml.safe_load(f)


# Instantiate storage objects
token_storages = {}
global_storage = Storage(config['global_store'])
for token, path in config['token_stores'].items():
    token_storages[token] = Storage(path)


_endpoint_template = """
async def {name}(
        data: Annotated[{model_var_name}.{type}, Form(), {info}],
        x_dumpthings_token: Annotated[str | None, Header()]
):
    print('endpoint[{name}]:', data.model_dump())
    print('Token:', x_dumpthings_token)
    lgr.info('endpoint[{name}]: %s', data)
    return handle_record('{label}', data, x_dumpthings_token)
"""


def handle_record(
    label: str,
    data: BaseModel,
    token: str | None,
) -> Any:
    if token is None:
        return None
    token_storages[token].store_record(record=data, label=label)
    return data


lgr = logging.getLogger('uvicorn')


# Create pydantic models from schema sources and add them to globals
model_info = {}
model_counter = count()
for label, configuration in global_storage.collections.items():
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


@app.get('/{label}/find/{identifier}')
async def read_item(
    label: str,
    identifier: str,
    x_dumpthings_token: Annotated[str | None, Header()] = None
):
    if x_dumpthings_token is not None:
        store = token_storages.get(x_dumpthings_token, None)
        if store:
            record = store.get_record(label, identifier)
            if record:
                return record
    return global_storage.get_record(label, identifier)


@app.get('/{label}/record/{type_name}')
def read_item(
    label: str,
    type_name: str,
    x_dumpthings_token: Annotated[str | None, Header()] = None
):
    records = {}
    if x_dumpthings_token is not None:
        store = token_storages.get(x_dumpthings_token, None)
        if store:
            for record in store.get_all_records(label, type_name):
                records[record['id']] = record
    for record in global_storage.get_all_records(label, type_name):
        records[record['id']] = record
    yield from records.values()


app.openapi_schema = None
app.setup()
