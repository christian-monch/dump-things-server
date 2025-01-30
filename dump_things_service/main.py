import logging
import os
from itertools import count
from typing import Annotated

import yaml
from fastapi import FastAPI, Form

from dump_things_service.model import build_model, get_classes
from dump_things_service.storage import Storage


config_file = os.environ.get('DUMPTHINGS_CONFIG_FILE', './dumpthings_conf.yaml')
with open(config_file, 'rt') as f:
    config = yaml.safe_load(f)


schema_ids = config['schema_ids']
storage_path = config['storage_path']


global_storage = Storage(storage_path, create_new_ok=True)


_endpoint_template = """
async def {name}(data: Annotated[model.{type}, Form(), {info}]):
    print('endpoint[{name}]:', data.model_dump())
    lgr.info('endpoint[{name}]: %s', data)
    global_storage.store_record(record=data, schema_id='{id}')
    return data
"""


lgr = logging.getLogger('uvicorn')


# Create pydantic models from schema sources
models = {}
for schema_id in schema_ids:
    lgr.info('Building model from %s.', schema_id)
    model = build_model(schema_id)
    classes = get_classes(model)
    models[schema_id] = model.linkml_meta['name'], model.version, model, classes


app = FastAPI()


# Create endpoints for all applications, all versions, and all classes
lgr.info('Creating dynamic endpoints...')
serial_number = count()


for schema_id, (name, version, model, classes) in models.items():
    for type_name in classes:
        # Create an endpoint to dump data of type `type_name` in version
        # `version` of schema `application`.
        endpoint_name = f'_endpoint_{next(serial_number)}'
        exec(_endpoint_template.format(
            name=endpoint_name,
            type=type_name,
            id=schema_id,
            info=f"'endpoint for {name}/{version}/{type_name}'"
        ))
        endpoint = locals()[endpoint_name]

        # Create an API route for the endpoint
        app.add_api_route(
            path=f'/dump/{name}/{version}/{type_name}',
            endpoint=locals()[endpoint_name],
            methods=['POST'],
            name=f'handle "{type_name}" of schema "{model.linkml_meta["id"]}" objects',
            response_model=getattr(model, type_name)
        )

lgr.info('Creation of %d endpoints completed.', next(serial_number))

app.openapi_schema = None
app.setup()
