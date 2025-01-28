from collections import defaultdict
from itertools import count
from typing import Annotated

from fastapi import FastAPI, Form

from model import build_model, get_classes


schema_sources = {
    'trr379': ['https://concepts.trr379.de/s/base/unreleased.yaml'],
}


_endpoint_template = """
def {name}(data: Annotated[model.{type}, Form(), {info}]):
    print('endpoint[{name}]:', data.model_dump())
    return data
"""


models = defaultdict(dict)

# Create pydantic models
for schema_name, schema_urls in schema_sources.items():
    for schema_url in schema_urls:
        model = build_model(schema_url)
        classes = get_classes(model)
        models[schema_name][model.version] = model, classes


app = FastAPI()


# Create endpoints for all applications, all versions, and all classes
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


app.openapi_schema = None
app.setup()
