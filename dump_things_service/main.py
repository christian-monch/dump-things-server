from typing import Annotated

from fastapi import FastAPI, Form
from pydantic import BaseModel
from itertools import count

from model import build_model, get_classes



# Create pydantic models

model = build_model('https://concepts.trr379.de/s/base/unreleased.yaml')
classes = get_classes(model)
print(classes)


app = FastAPI()



class FormData(BaseModel):
    name: str
    email: str
    zusage: str
    food: str
    infos: str
    model_config = {"extra": "forbid"}


_endpoint_template = """
def {name}(data: Annotated[model.{type}, Form(), {info}]):
    print('endpoint[{name}]:', data.model_dump())
    return data
"""

serial_number = count()


for type_name in classes:
    endpoint_name = f'_endpoint_{next(serial_number)}'
    exec(_endpoint_template.format(
        name=endpoint_name,
        type=type_name,
        info=f"'endpoint {endpoint_name} to dump {type_name}'"
    ))
    app.add_api_route(
        path=f'/dump/{type_name}',
        endpoint=locals()[endpoint_name],
        methods=['POST'],
        name=f'Added endpoint "{endpoint_name}" to receive "{type_name}" objects',
        response_model=getattr(model, type_name)
    )

app.openapi_schema = None
app.setup()
