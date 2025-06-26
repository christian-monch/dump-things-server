from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import (
    cast,
    Any,
    Optional,
)

import strawberry
import uvicorn
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from strawberry.asgi import GraphQL

from dump_things_service.config import Config, get_mapping_function
from dump_things_service.graphql.sdl import get_strawberry_module_for_linkml_schema
from dump_things_service.graphql.resolvers import (
    get_record_by_pid,
    get_all_records,
    get_records_by_class_name,
)
from dump_things_service.model import get_model_for_schema
from dump_things_service.record import RecordDirStore


logger = logging.getLogger('dump_things_service.graphql')
uvicorn_logger = logging.getLogger('uvicorn')


parser = argparse.ArgumentParser()
parser.add_argument('--host', default='0.0.0.0')  # noqa S104
parser.add_argument('--port', default=8000, type=int)
parser.add_argument('--origins', action='append', default=['*'])
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
    'config_dir',
    help='Directory that contains the config file for store.',
)
parser.add_argument(
    'store',
    help='The directory that stores the records.',
)

arguments = parser.parse_args()

# Set the log level
numeric_level = getattr(logging, arguments.log_level.upper(), None)
if not isinstance(numeric_level, int):
    logger.error('Invalid log level: %s, defaulting to level "WARNING"', arguments.log_level)
    numeric_level = getattr(logging, 'WARNING', None)

logging.basicConfig(level=numeric_level)


# The next steps generate the GraphQL module. This is needed for the
# resolver-signatures.
config_dir = Path(arguments.config_dir)
record_root_dir = Path(arguments.store)
config = Config.get_collection_dir_config(config_dir)
graphql_module = get_strawberry_module_for_linkml_schema(config.schema)
linkml_model, classes, model_var_name = get_model_for_schema(config.schema)

AllThings = graphql_module.AllThings
AllRecords = graphql_module.AllRecords
ClassNames = graphql_module.ClassNames


store = RecordDirStore(
    root=record_root_dir,
    model=linkml_model,
    pid_mapping_function=get_mapping_function(config),
    suffix=config.format,
)


def resolve_pid(pid: strawberry.ID) -> AllThings | None:
    global store
    return cast(AllThings, get_record_by_pid(graphql_module, store, pid))


def resolve_all() -> list[AllRecords]:
    global store
    return list(get_all_records(graphql_module, store))


def resolve_records(class_name: ClassNames) -> list[AllThings]:
    global store
    return list(get_records_by_class_name(graphql_module, store, class_name.value))


def server() -> None:
    host = arguments.host
    port = arguments.port

    # Windows doesn't support UTF-8 by default
    endl = " 🍓\n" if sys.platform != "win32" else "\n"
    print(
        f'Running strawberry on http://{host}:{port}/graphql,\n'
        f'  store: {record_root_dir}\n'
        f'  config dir: {config_dir}\n'
        f'  schema: {config.schema}\n',
        end=endl
    )

    app = Starlette(debug=True)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=arguments.origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    @strawberry.type
    class Query:
        record: Optional[AllThings] = strawberry.field(resolver=resolve_pid)
        all: list[AllRecords] = strawberry.field(resolver=resolve_all)
        records: list[AllThings] = strawberry.field(resolver=resolve_records)

    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQL[Any, Any](schema, debug=True)

    paths = ["/", "/graphql"]
    for path in paths:
        app.add_route(path, graphql_app)  # type: ignore
        app.add_websocket_route(path, graphql_app)  # type: ignore

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=numeric_level,
    )


if __name__ == "__main__":
    server()
