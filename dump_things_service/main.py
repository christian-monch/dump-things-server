import logging
import os
from itertools import count
from typing import Annotated

import yaml
from fastapi import FastAPI, Form

from dump_things_service.model import build_model, get_classes
from dump_things_service.storage import Storage


storage_path = os.environ.get('DUMP_THINGS_STORAGE_PATH', None)
if storage_path is None:
    msg = 'The environment variable DUMP_THINGS_STORAGE_PATH must be set.'
    raise RuntimeError(msg)
global_storage = Storage(storage_path)


_endpoint_template = """
async def {name}(data: Annotated[{model_var_name}.{type}, Form(), {info}]):
    print('endpoint[{name}]:', data.model_dump())
    lgr.info('endpoint[{name}]: %s', data)
    global_storage.store_record(record=data, label='{label}')
    return data
"""


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

app.openapi_schema = None
app.setup()
