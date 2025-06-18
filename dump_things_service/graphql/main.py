from __future__ import annotations

import sys
from enum import Enum
from typing import (
    Any,
    Optional,
)

import strawberry
import uvicorn
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from strawberry.asgi import GraphQL

from dump_things_service.graphql.sdl import get_strawberry_module_for_linkml_schema


module = get_strawberry_module_for_linkml_schema(sys.argv[1])


AllThings = module.AllThings
AllRecords = module.AllRecords
Agent = module.Agent
Person = module.Person
Thing = module.Thing
ClassNames = module.ClassNames


def resolve_pid(pid: strawberry.ID) -> AllThings | None:
    if pid.lower().startswith('person'):
        return Person(
            pid=strawberry.ID(pid),
            given_name=f'John-{{pid}}',
        )
    elif pid.lower().startswith('agent'):
        return Agent(
            pid=strawberry.ID(pid),
            at_location=f'Berlin-{{pid}}',
        )
    else:
        return Thing(
            pid=strawberry.ID(pid),
            description=f'Thing description for {{pid}}',
        )


def resolve_all() -> list[AllRecords]:
    return [
        Agent(pid=strawberry.ID('agent-1'), at_location='Berlin'),
        Person(pid=strawberry.ID('person-1'), given_name='John'),
        Thing(pid=strawberry.ID('thing-1'), description='A sample thing'),
    ]


def resolve_records(class_name: ClassNames) -> list[AllThings]:
    return [
        Agent(pid=strawberry.ID('agent-1'), at_location=f'Berlin {{class_name}}'),
        Agent(pid=strawberry.ID('agent-2'), at_location=f'Berlin {{class_name}}'),
        Agent(pid=strawberry.ID('agent-3'), at_location=f'Berlin {{class_name}}'),
    ]


class LogLevel(str, Enum):
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"

    __slots__ = ()


def server(
        linkml_schema: str,
        host: str = '0.0.0.0',
        port: int = 8000,
        log_level: LogLevel = LogLevel.debug,
) -> None:


    # Windows doesn't support UTF-8 by default
    endl = " 🍓\n" if sys.platform != "win32" else "\n"
    print(f"Running strawberry on http://{host}:{port}/graphql", end=endl)  # noqa: T201

    app = Starlette(debug=True)
    app.add_middleware(
        CORSMiddleware, allow_headers=["*"], allow_origins=["*"], allow_methods=["*"]
    )

    module = get_strawberry_module_for_linkml_schema(linkml_schema)
    @strawberry.type
    class Query:
        record: Optional[module.AllThings] = strawberry.field(resolver=resolve_pid)
        all: list[module.AllRecords] = strawberry.field(resolver=resolve_all)
        records: list[module.AllThings] = strawberry.field(resolver=resolve_records)

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
