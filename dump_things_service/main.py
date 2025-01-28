import logging
from collections import defaultdict
from itertools import count
from typing import Annotated

from yaml import (
    SafeLoader,
    load,
)
from fastapi import FastAPI, Form

from .model import build_model, get_classes
from .storage import store_data


schema_sources = ['https://concepts.trr379.de/s/base/unreleased.yaml']


_endpoint_template = """
def {name}(data: Annotated[model.{type}, Form(), {info}]):
    print('endpoint[{name}]:', data.model_dump())
    return data
"""


lgr = logging.getLogger('uvicorn')

models = defaultdict(dict)

# Create pydantic models
for schema_source in schema_sources:
    lgr.info('Building model from %s.', schema_source)
    model = build_model(schema_source)
    classes = get_classes(model)
    models[model.linkml_meta['name']][model.version] = model, classes


app = FastAPI()


# Create endpoints for all applications, all versions, and all classes
lgr.info('Creating dynamic endpoints...')
serial_number = count()
for application, app_info in models.items():
    for version, (model, classes) in app_info.items():
        for type_name in classes:
            # Create an endpoint to dump data of type `type_name` in version
            # `version` of schema `application`.
            endpoint_name = f'_endpoint_{next(serial_number)}'
            exec(_endpoint_template.format(
                name=endpoint_name,
                type=type_name,
                info=f"'endpoint for {application}/{version}/{type_name}'"
            ))
            endpoint = locals()[endpoint_name]

            # Create an API route for the endpoint
            app.add_api_route(
                path=f'/dump/{application}/{version}/{type_name}',
                endpoint=locals()[endpoint_name],
                methods=['POST'],
                name=f'Added "{endpoint_name}" to handle "{application}/{version}/{type_name}" objects',
                response_model=getattr(model, type_name)
            )

lgr.info('Creation of %d endpoints completed.', next(serial_number))

app.openapi_schema = None
app.setup()
