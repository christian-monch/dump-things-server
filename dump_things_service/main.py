from __future__ import annotations

import argparse
import logging
from itertools import count
from typing import (
    TYPE_CHECKING,
    Annotated,  # noqa F401 -- used by generated code
    Iterable,  # noqa F401 -- used by generated code
)

import uvicorn
from fastapi import (
    Body,  # noqa F401 -- used by generated code
    Depends,
    FastAPI,
    HTTPException,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from starlette.responses import (
    JSONResponse,
    PlainTextResponse,
)

from dump_things_service import Format
from dump_things_service.backends.filesystem_records import FileSystemRecords

if TYPE_CHECKING:
    from pydantic import BaseModel


lgr = logging.getLogger('uvicorn')

parser = argparse.ArgumentParser()
parser.add_argument('--host', default='0.0.0.0')  # noqa S104
parser.add_argument('--port', default=8000, type=int)
parser.add_argument('--origins', action='append', default=[])
parser.add_argument(
    'store',
    help='The root of the data stores, it should contain a global_store and token_stores.',
)

arguments = parser.parse_args()


# Instantiate storage objects
store = FileSystemRecords(arguments.store)


_endpoint_template = """
async def {name}(
        data: {model_var_name}.{class_name} | Annotated[str, Body(media_type='text/plain')],
        api_key: str = Depends(api_key_header_scheme),
        format: Format = Format.json,
) -> JSONResponse | PlainTextResponse:
    lgr.info('{name}(%s, %s, %s, %s, %s)', repr(data), repr('{class_name}'), repr(format), repr(api_key))
    return store_record('{collection}', data, '{class_name}', format, api_key)
"""


def store_record(
    collection: str,
    data: BaseModel | str,
    class_name: str,
    input_format: Format,
    token: str | None,
) -> JSONResponse | PlainTextResponse:
    if input_format == Format.json and isinstance(data, str):
        raise HTTPException(status_code=404, detail='Invalid JSON data provided.')

    if input_format == Format.ttl and not isinstance(data, str):
        raise HTTPException(status_code=404, detail='Invalid ttl data provided.')

    return JSONResponse([
        record.model_dump(exclude_none=True)
        for record in store.store(
            collection=collection,
            record=data,
            authorization_info = token,
        )
    ])


app = FastAPI()
api_key_header_scheme = APIKeyHeader(
    name='X-DumpThings-Token',
    # authentication is generally optional
    auto_error=False,
    scheme_name='submission',
    description='Presenting a valid token enables record submission, and retrieval of records submitted with this token prior curation.',
)

# Add CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=arguments.origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


# Create endpoints for all applications, all versions, and all classes
lgr.info('Creating dynamic endpoints...')

serial_number = count()
for collection_name, collection_info in store.collections.items():
    for class_name in collection_info.classes:
        # Create an endpoint to dump data of type `class_name` in version
        # `version` of schema `application`.
        endpoint_name = f'_endpoint_{next(serial_number)}'
        model_var_name = f'_{collection_name}_model'
        globals()[model_var_name] = collection_info.model

        endpoint_source = _endpoint_template.format(
            name=endpoint_name,
            model_var_name=model_var_name,
            class_name=class_name,
            collection=collection_name,
            info=f"'store {collection_name}/{class_name} objects'",
        )
        exec(endpoint_source)  # noqa S102
        endpoint = locals()[endpoint_name]

        # Create an API route for the endpoint
        app.add_api_route(
            path=f'/{collection_name}/record/{class_name}',
            endpoint=locals()[endpoint_name],
            methods=['POST'],
            name=f'handle "{class_name}" of schema "{collection_info.model.linkml_meta["id"]}" objects',
            response_model=getattr(collection_info.model, class_name),
        )

lgr.info('Creation of %d endpoints completed.', next(serial_number))


@app.get('/{collection}/record')
async def read_record_with_id(
    collection: str,
    id: str,  # noqa A002
    format: Format = Format.json,  # noqa A002
    api_key: str = Depends(api_key_header_scheme),
):
    record = store.record_with_id(collection, id, api_key)
    if record:
        return JSONResponse(record.model_dump(exclude_none=True))
    return None


@app.get('/{collection}/records/{class_name}')
async def read_records_of_type(
    collection: str,
    class_name: str,
    format: Format = Format.json,  # noqa A002
    api_key: str = Depends(api_key_header_scheme),
):
    return JSONResponse([
        record.model_dump(exclude_none=True)
        for record in store.records_of_class(collection, class_name, api_key)
    ])


# Rebuild the app to include all dynamically created endpoints
app.openapi_schema = None
app.setup()


if __name__ == '__main__':
    uvicorn.run(
        app,
        host=arguments.host,
        port=arguments.port,
    )
