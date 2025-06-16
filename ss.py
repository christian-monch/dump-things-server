from __future__ import annotations

import strawberry
from enum import Enum
from typing import Annotated
from typing import NewType
from typing import Union

AllThings = Annotated[
    Union[
        'Thing',
        'Person',
    ],
    strawberry.union(name="AllThings")
]

curie = strawberry.scalar(NewType("curie", object), serialize=lambda v: v, parse_value=lambda v: v)

date = strawberry.scalar(NewType("date", object), serialize=lambda v: v, parse_value=lambda v: v)

date_or_datetime = strawberry.scalar(NewType("date_or_datetime", object), serialize=lambda v: v, parse_value=lambda v: v)

datetime = strawberry.scalar(NewType("datetime", object), serialize=lambda v: v, parse_value=lambda v: v)

decimal = strawberry.scalar(NewType("decimal", object), serialize=lambda v: v, parse_value=lambda v: v)

double = strawberry.scalar(NewType("double", object), serialize=lambda v: v, parse_value=lambda v: v)

EmailAddress = strawberry.scalar(NewType("EmailAddress", object), serialize=lambda v: v, parse_value=lambda v: v)

HexBinary = strawberry.scalar(NewType("HexBinary", object), serialize=lambda v: v, parse_value=lambda v: v)

jsonpath = strawberry.scalar(NewType("jsonpath", object), serialize=lambda v: v, parse_value=lambda v: v)

jsonpointer = strawberry.scalar(NewType("jsonpointer", object), serialize=lambda v: v, parse_value=lambda v: v)

ncname = strawberry.scalar(NewType("ncname", object), serialize=lambda v: v, parse_value=lambda v: v)

nodeidentifier = strawberry.scalar(NewType("nodeidentifier", object), serialize=lambda v: v, parse_value=lambda v: v)

NodeUriOrCurie = strawberry.scalar(NewType("NodeUriOrCurie", object), serialize=lambda v: v, parse_value=lambda v: v)

NonNegativeInteger = strawberry.scalar(NewType("NonNegativeInteger", object), serialize=lambda v: v, parse_value=lambda v: v)

objectidentifier = strawberry.scalar(NewType("objectidentifier", object), serialize=lambda v: v, parse_value=lambda v: v)

sparqlpath = strawberry.scalar(NewType("sparqlpath", object), serialize=lambda v: v, parse_value=lambda v: v)

time = strawberry.scalar(NewType("time", object), serialize=lambda v: v, parse_value=lambda v: v)

uri = strawberry.scalar(NewType("uri", object), serialize=lambda v: v, parse_value=lambda v: v)

uriorcurie = strawberry.scalar(NewType("uriorcurie", object), serialize=lambda v: v, parse_value=lambda v: v)

W3CISO8601 = strawberry.scalar(NewType("W3CISO8601", object), serialize=lambda v: v, parse_value=lambda v: v)

@strawberry.interface
class ThingMixin:
    broad_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    description: str | None
    exact_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None

@strawberry.type
class Person:
    pid: strawberry.ID
    relations: list[AllThings] | None
    friends: list[Thing] | None
    description: str | None
    annotations: list[Thing | None] | None

@strawberry.type
class Thing(ThingMixin):
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Person | None] | None


@strawberry.type
class Query:
    record: AllThings | None
    records: list[AllThings]

schema = strawberry.Schema(query=Query)
