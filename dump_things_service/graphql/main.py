from __future__ import annotations

import sys
from enum import Enum
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

from dump_things_service.graphql.sdl import get_strawberry_module_for_linkml_schema
from dump_things_service.config import Config
from dump_things_service.record import RecordDirStore



record_dir_root = sys.argv[1]  # '/home/cristian/tmp/dumpthings/store_new/flatusers'
record_dir_root = Path(record_dir_root)
config = Config.get_collection_dir_config(record_dir_root)

module = get_strawberry_module_for_linkml_schema(config.schema)

from dump_thing_service_graphql_strawberry_module import (
    AllThings,
    AllRecords,
    ClassNames,
)


from dump_things_service.graphql.resolvers import (
    get_all_records,
    get_record_by_pid,
    get_records_by_class_name,
)



def resolve_pid(pid: strawberry.ID) -> AllThings | None:
    return cast(AllThings, get_record_by_pid(module, pid))


def resolve_all() -> list[AllRecords]:
    return cast(list[AllRecords], get_all_records(module))


def resolve_records(class_name: ClassNames) -> list[AllThings]:
    records = get_records_by_class_name(module, class_name)
    return cast(list[AllThings], records)


class LogLevel(str, Enum):
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"


def server(
        record_dir_root: str,
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
    server(sys.argv[1])
