from __future__ import annotations

import argparse
import logging
from functools import cached_property
from pathlib import Path
from typing import (
    cast,
    Optional,
)

import strawberry
import uvicorn
from click import Context
from dns.tsig import get_context
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from strawberry.fastapi import (
    BaseContext,
    GraphQLRouter,
)

from dump_things_service import config_file_name
from dump_things_service.config import process_config
from dump_things_service.common import check_collection
from dump_things_service.graphql.sdl import get_strawberry_module_for_linkml_schema
from dump_things_service.graphql.resolvers import (
    get_record_by_pid,
    get_all_records,
    get_records_by_class_name,
)


logger = logging.getLogger('dump_things_service.graphql')
uvicorn_logger = logging.getLogger('uvicorn')


parser = argparse.ArgumentParser()
parser.add_argument('--host', default='0.0.0.0')  # noqa S104
parser.add_argument('--port', default=8000, type=int)
parser.add_argument('--origins', action='append', default=['*'])
parser.add_argument('-c', '--config')
parser.add_argument(
    '--root-path',
    default='',
    help="Set the ASGI 'root_path' for applications submounted below a given URL path.",
)
parser.add_argument(
    '--log-level',
    default='WARNING',
    help="Set the log level for the service, allowed values are 'ERROR', 'WARNING', 'INFO', 'DEBUG'. Default is 'warning'.",
)
parser.add_argument(
    'store',
    help='The directory that stores the records.',
)
parser.add_argument(
    'collection',
    help='Collection that should be queried.',
)

arguments = parser.parse_args()

# Set the log level
numeric_level = getattr(logging, arguments.log_level.upper(), None)
if not isinstance(numeric_level, int):
    logger.error('Invalid log level: %s, defaulting to level "WARNING"', arguments.log_level)
    numeric_level = getattr(logging, 'WARNING', None)

logging.basicConfig(level=numeric_level)


store_path = Path(arguments.store)
config_path = Path(arguments.config) if arguments.config else store_path / config_file_name
g_instance_config = process_config(
    store_path=store_path,
    config_file=config_path,
    order_by=['pid'],
    globals_dict=globals(),
)
check_collection(g_instance_config, arguments.collection)

# The next steps generate the GraphQL module. This is needed for the
# resolver-signatures.
schema = g_instance_config.schemas[arguments.collection]
graphql_module = get_strawberry_module_for_linkml_schema(schema)
linkml_model, classes, model_var_name = g_instance_config.model_info[arguments.collection]

AllThings = graphql_module.AllThings
AllRecords = graphql_module.AllRecords
ClassNames = graphql_module.ClassNames


class Context(BaseContext):
    @cached_property
    def token(self) -> str | None:
        if not self.request:
            return None
        return self.request.headers.get('X-Dumpthings-Token', None)


def resolve_pid(pid: strawberry.ID, info: strawberry.Info[Context]) -> AllThings | None:
    return cast(AllThings, get_record_by_pid(
        g_instance_config,
        arguments.collection,
        graphql_module,
        pid,
        info.context,
    ))


def resolve_all(info: strawberry.Info[Context]) -> list[AllRecords]:
    return list(get_all_records(
        g_instance_config,
        arguments.collection,
        graphql_module,
        info.context
    ))


def resolve_records(class_name: ClassNames, info: strawberry.Info[Context]) -> list[AllThings]:
    global store
    return list(get_records_by_class_name(
        g_instance_config,
        arguments.collection,
        graphql_module,
        class_name.value,
        info.context,
    ))


@strawberry.type
class Query:
    record: Optional[AllThings] = strawberry.field(resolver=resolve_pid)
    all: list[AllRecords] = strawberry.field(resolver=resolve_all)
    records: list[AllThings] = strawberry.field(resolver=resolve_records)


async def get_context() -> Context:
    return Context()


def server() -> None:
    host = arguments.host
    port = arguments.port

    print(
        f'Running strawberry on http://{host}:{port}/graphql,\n'
        f'  store: {store_path}\n'
        f'  collection: {arguments.collection}\n'
        f'  schema: {g_instance_config.schemas[arguments.collection]}\n',
    )

    app = FastAPI(debug=True) # Starlette(debug=True)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=arguments.origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    graphql_schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter(graphql_schema, context_getter=get_context)

    paths = ["/graphql"]
    for path in paths:
        app.include_router(graphql_app, prefix=path)

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=numeric_level,
    )


if __name__ == "__main__":
    server()
