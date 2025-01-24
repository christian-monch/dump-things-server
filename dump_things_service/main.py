from typing import Annotated

from fastapi import FastAPI, Form, Query
#from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()


class FormData(BaseModel):
    name: str
    email: str
    zusage: str
    food: str
    infos: str
    model_config = {"extra": "forbid"}

#app.mount("/demos", StaticFiles(directory="demos"), name="demos")

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
