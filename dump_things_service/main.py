from __future__ import annotations

import argparse
import logging
import sys
from functools import partial
from itertools import count
from pathlib import Path
from typing import (
    Annotated,  # noqa F401 -- used by generated code
    Any,
)

import uvicorn
from fastapi import (
    Body,  # noqa F401 -- used by generated code
    Depends,
    FastAPI,
    HTTPException,
)
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import (
    BaseModel,
    TypeAdapter,
    ValidationError,
)
from starlette.responses import (
    JSONResponse,
    PlainTextResponse,
)

from dump_things_service import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    Format,
    config_file_name,
)
from dump_things_service.config import (
    get_default_token_name,
    get_token_store,
    get_zone,
    join_default_token_permissions,
    process_config,
)
from dump_things_service.convert import (
    convert_json_to_ttl,
    convert_ttl_to_json,
)
from dump_things_service.dynamic_endpoints import create_endpoints
from dump_things_service.model import (
    get_classes,
    get_subclasses,
)
from dump_things_service.record import RecordDirStore
from dump_things_service.utils import (
    cleaned_json,
    combine_ttl,
)


class TokenCapabilityRequest(BaseModel):
    token: str | None


parser = argparse.ArgumentParser()
parser.add_argument('--host', default='0.0.0.0')  # noqa S104
parser.add_argument('--port', default=8000, type=int)
parser.add_argument('--origins', action='append', default=[])
parser.add_argument('-c', '--config')
parser.add_argument(
    '--root-path',
    default='',
    help="Set the ASGI 'root_path' for applications submounted below a given URL path.",
)
parser.add_argument(
    'store',
    help='The root of the data stores, it should contain a global_store and token_stores.',
)

arguments = parser.parse_args()

lgr = logging.getLogger('uvicorn')

store_path = Path(arguments.store)

g_error = None

config_path = Path(arguments.config) if arguments.config else store_path / config_file_name
try:
    g_instance_config = process_config(
        store_path=store_path,
        config_file=config_path,
        globals_dict=globals(),
    )
except ValidationError as e:
    lgr.error(
        'ERROR: invalid configuration file at: `%s`:\n%s',
        config_path,
        str(e),
    )
    g_error = 'Invalid configuration file. See server error-log for details.'
    sys.exit(1)


api_key_header_scheme = APIKeyHeader(
    name='X-DumpThings-Token',
    # authentication is generally optional
    auto_error=False,
    scheme_name='submission',
    description='Presenting a valid token enables record submission, and retrieval of records submitted with this token prior curation.',
)


def handle_global_error():
    if g_error:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=g_error)


def store_record(
    collection: str,
    data: BaseModel | str,
    class_name: str,
    model: Any,
    input_format: Format,
    api_key: str | None = Depends(api_key_header_scheme),
) -> JSONResponse | PlainTextResponse:
    if input_format == Format.json and isinstance(data, str):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail='Invalid JSON data provided.'
        )

    if input_format == Format.ttl and not isinstance(data, str):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail='Invalid ttl data provided.'
        )

    token = get_default_token_name(g_instance_config, collection) if api_key is None else api_key
    # Get the token permissions and extend them by the default permissions
    store, token_permissions = get_token_store(g_instance_config, collection, token)
    final_permissions = join_default_token_permissions(g_instance_config, token_permissions, collection)
    if not final_permissions.incoming_write:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f'Not authorized to submit to collection "{collection}".',
        )

    if input_format == Format.ttl:
        json_object = convert_ttl_to_json(
            g_instance_config,
            collection,
            class_name,
            data,
        )
        record = TypeAdapter(getattr(model, class_name)).validate_python(json_object)
    else:
        record = data

    stored_records = store.store_record(
        record=record,
        submitter_id=g_instance_config.token_stores[token]['user_id'],
        model=model,
    )

    if input_format == Format.ttl:
        return PlainTextResponse(
            combine_ttl(
                [
                    convert_json_to_ttl(
                        g_instance_config,
                        collection,
                        record.__class__.__name__,
                        cleaned_json(
                            record.model_dump(mode='json', exclude_none=True),
                            remove_keys=('@type', 'schema_type'),
                        )
                    )
                    for record in stored_records
                ]
            ),
            media_type='text/turtle',
        )
    return JSONResponse(
        list(
            map(
                partial(cleaned_json, remove_keys=('@type', 'schema_type')),
                map(jsonable_encoder, stored_records),
            )
        )
    )


app = FastAPI()

# Add CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=arguments.origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.post('/{collection}/token_permissions')
async def fetch_token_permissions(
    collection: str,
    body: TokenCapabilityRequest,
):
    token = get_default_token_name(g_instance_config, collection) if body.token is None else body.token
    token_store, token_permissions = get_token_store(g_instance_config, collection, token)
    final_permissions = join_default_token_permissions(g_instance_config, token_permissions, collection)
    return JSONResponse(
        {
            'read_curated': final_permissions.curated_read,
            'read_incoming': final_permissions.incoming_read,
            'write_incoming': final_permissions.incoming_write,
            **(
                {'incoming_zone': get_zone(g_instance_config, collection, token)}
                if final_permissions.incoming_read or final_permissions.incoming_write
                else {}
            ),
        }
    )


@app.get('/{collection}/record')
async def read_record_with_pid(
    collection: str,
    pid: str,
    format: Format = Format.json,  # noqa A002
    api_key: str = Depends(api_key_header_scheme),
):
    token = get_default_token_name(g_instance_config, collection) if api_key is None else api_key

    token_store, token_permissions = get_token_store(g_instance_config, collection, token)
    final_permissions = join_default_token_permissions(g_instance_config, token_permissions, collection)
    if not final_permissions.curated_read and not final_permissions.incoming_read:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f'No read access to curated or incoming data in collection "{collection}".',
        )

    record = None
    if final_permissions.incoming_read:
        class_name, record = token_store.get_record_by_pid(pid)

    if not record and final_permissions.curated_read:
        class_name, record = g_instance_config.curated_stores[collection].get_record_by_pid(pid)

    record = cleaned_json(record, remove_keys=('@type', 'schema_type'))
    if record and format == Format.ttl:
        ttl_record = convert_json_to_ttl(
            g_instance_config,
            collection,
            class_name,
            record,
        )
        return PlainTextResponse(ttl_record, media_type='text/turtle')
    return record


@app.get('/{collection}/records/{class_name}')
async def read_records_of_type(
    collection: str,
    class_name: str,
    format: Format = Format.json,  # noqa A002
    api_key: str = Depends(api_key_header_scheme),
):
    token = get_default_token_name(g_instance_config, collection) if api_key is None else api_key

    model = g_instance_config.model_info[collection][0]
    if class_name not in get_classes(model):
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f'No "{class_name}"-class in collection "{collection}".',
        )

    token_store, token_permissions = get_token_store(g_instance_config, collection, token)
    final_permissions = join_default_token_permissions(g_instance_config, token_permissions, collection)
    if not final_permissions.incoming_read and not final_permissions.curated_read:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f'No read access to curated or incoming data in collection "{collection}".',
        )

    records = {}
    if final_permissions.curated_read:
        for search_class_name in get_subclasses(model, class_name):
            for record_class_name, record in g_instance_config.curated_stores[collection].get_records_of_class(
                search_class_name
            ):
                records[record['pid']] = record_class_name, record

    if final_permissions.incoming_read:
        for search_class_name in get_subclasses(model, class_name):
            for record_class_name, record in token_store.get_records_of_class(search_class_name):
                records[record['pid']] = record_class_name, record

    if format == Format.ttl:
        ttls = [
            convert_json_to_ttl(
                g_instance_config,
                collection,
                target_class=record_class_name,
                json=cleaned_json(record, remove_keys=('@type', 'schema_type')),
            )
            for record_class_name, record in records.values()
        ]
        if ttls:
            return PlainTextResponse(combine_ttl(ttls), media_type='text/turtle')
        return PlainTextResponse('', media_type='text/turtle')
    return [
        cleaned_json(record, remove_keys=('@type', 'schema_type'))
        for _, record in records.values()
    ]


# Create dynamic endpoints and rebuild the app to include all dynamically
# created endpoints.
create_endpoints(app, g_instance_config, globals())
app.openapi_schema = None
app.setup()


if __name__ == '__main__':
    uvicorn.run(
        app,
        host=arguments.host,
        port=arguments.port,
        root_path=arguments.root_path,
    )
