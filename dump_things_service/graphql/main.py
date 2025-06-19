from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path
from typing import (
    cast,
    Any,
    Iterable,
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


# The next steps generate the GraphQL-module. This is needed for the resolver-
# signatures.
record_dir_root = Path(sys.argv[1])
config = Config.get_collection_dir_config(record_dir_root)
graphql_module = get_strawberry_module_for_linkml_schema(config.schema)
linkml_model, classes, model_var_name = get_model_for_schema(config.schema)

AllThings = graphql_module.AllThings
AllRecords = graphql_module.AllRecords
ClassNames = graphql_module.ClassNames


store = RecordDirStore(
    root=record_dir_root,
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


class LogLevel(str, Enum):
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"


def server(
        record_dir_root: Path,
        host: str = '0.0.0.0',
        port: int = 8000,
        log_level: LogLevel = LogLevel.debug,
) -> None:


    # Windows doesn't support UTF-8 by default
    endl = " 🍓\n" if sys.platform != "win32" else "\n"
    print(f"Running strawberry on http://{host}:{port}/graphql, using store: {config.schema}", end=endl)  # noqa: T201

    app = Starlette(debug=True)
    app.add_middleware(
        CORSMiddleware, allow_headers=["*"], allow_origins=["*"], allow_methods=["*"]
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
        log_level=log_level,
    )


if __name__ == "__main__":
    server(record_dir_root)
