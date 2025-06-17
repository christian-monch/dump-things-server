from __future__ import annotations
import sys
from typing import Any, Optional, Union

import strawberry
import uvicorn
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from strawberry import Schema
from strawberry.asgi import GraphQL

from dump_things_service.graphql.sdl import get_strawberry_module_for_linkml_schema


module = get_strawberry_module_for_linkml_schema(sys.argv[1])


import os
import sys
from enum import Enum


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

    assert isinstance(module.schema, Schema)
    graphql_app = GraphQL[Any, Any](module.schema, debug=True)

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
