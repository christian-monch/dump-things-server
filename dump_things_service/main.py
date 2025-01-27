from typing import Annotated

from fastapi import FastAPI, Form, Query
#from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.responses import JSONResponse
from itertools import count

from model import build_model, get_classes


model_version = {
    'a': ['1', '2', '3'],
    'b': ['1', '2', '3'],
    'c': ['1', '2', '3'],
}


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

#app.mount("/demos", StaticFiles(directory="demos"), name="demos")



class TestData1(BaseModel):
    td1_name: str
    td1_age: str


class TestData2(BaseModel):
    td2_points: str
    td2_edges: str


class TestData3(BaseModel):
    td2_x: int
    td2_y: int
    width: int
    height: int


_endpoint_template = """
def {name}(data: Annotated[{type}, Form(), {info}]):
    print('endpoint[{name}]:', data.model_dump())
    return data
"""

serial_number = count()

dynamic_endpoints = {
    '/dyna1': 'TestData1',
    '/dyna2': 'TestData2',
    '/dyna3': 'TestData3',
}


for path, type_name in dynamic_endpoints.items():
    endpoint_name = f'_endpoint_{next(serial_number)}'
    exec(_endpoint_template.format(
        name=endpoint_name,
        type=type_name,
        info=f"'endpoint {endpoint_name} to dump {type_name}'"
    ))
    app.add_api_route(
        path=path,
        endpoint=locals()[endpoint_name],
        methods=['POST'],
        name=f'Added endpoint {endpoint_name} to receive {type_name}',
        response_model=locals()[type_name]
    )


def endpoint1(data: Annotated[FormData, Form(), 'our form']):
    print('endpoint1', data.model_dump())
    return data


app.add_api_route(
    path='/x',
    endpoint=endpoint1,
    methods=['POST'],
    name='Added endpoint',
    response_model=FormData
)
app.openapi_schema = None
app.setup()




class X:
    def __init__(self, v):
        self.v = v


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/submit/")
async def submit(data: Annotated[FormData, Form(), 'our form']):
    print(data)
    print(type(data))
    print(repr(data))
    print(data.model_dump())
    dump = data.model_dump()
    with open('/tmp/rsvp.tsv', 'ta') as fp:
        fp.write('{name}\t{email}\t{zusage}\t{food}\t{infos}\n'.format(**dump))
    return data
