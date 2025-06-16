import strawberry
from typing import NewType

curie = strawberry.scalar(NewType("curie", object), serialize=lambda v: v, parse_value=lambda v: v)

date = strawberry.scalar(NewType("date", object), serialize=lambda v: v, parse_value=lambda v: v)

date_or_datetime = strawberry.scalar(NewType("date_or_datetime", object), serialize=lambda v: v, parse_value=lambda v: v)

datetime = strawberry.scalar(NewType("datetime", object), serialize=lambda v: v, parse_value=lambda v: v)

decimal = strawberry.scalar(NewType("decimal", object), serialize=lambda v: v, parse_value=lambda v: v)

double = strawberry.scalar(NewType("double", object), serialize=lambda v: v, parse_value=lambda v: v)

jsonpath = strawberry.scalar(NewType("jsonpath", object), serialize=lambda v: v, parse_value=lambda v: v)

jsonpointer = strawberry.scalar(NewType("jsonpointer", object), serialize=lambda v: v, parse_value=lambda v: v)

ncname = strawberry.scalar(NewType("ncname", object), serialize=lambda v: v, parse_value=lambda v: v)

nodeidentifier = strawberry.scalar(NewType("nodeidentifier", object), serialize=lambda v: v, parse_value=lambda v: v)

objectidentifier = strawberry.scalar(NewType("objectidentifier", object), serialize=lambda v: v, parse_value=lambda v: v)

sparqlpath = strawberry.scalar(NewType("sparqlpath", object), serialize=lambda v: v, parse_value=lambda v: v)

time = strawberry.scalar(NewType("time", object), serialize=lambda v: v, parse_value=lambda v: v)

uri = strawberry.scalar(NewType("uri", object), serialize=lambda v: v, parse_value=lambda v: v)

uriorcurie = strawberry.scalar(NewType("uriorcurie", object), serialize=lambda v: v, parse_value=lambda v: v)

@strawberry.type
class Agent:
    relations: list[Thing | None] | None
    annotations: list[Annotation | None] | None
    pid: strawberry.ID
    schema_type: str | None
    acted_on_behalf_of: list[str | None] | None

@strawberry.type
class Annotation:
    annotation_tag: Thing
    annotation_value: str | None

@strawberry.type
class InstantaneousEvent:
    relations: list[Thing | None] | None
    annotations: list[Annotation | None] | None
    pid: strawberry.ID
    schema_type: str | None
    at_time: str | None

@strawberry.type
class Person:
    relations: list[Thing | None] | None
    annotations: list[Annotation | None] | None
    pid: strawberry.ID
    schema_type: str | None
    acted_on_behalf_of: list[str | None] | None
    given_name: str | None

@strawberry.type
class Thing:
    relations: list[Thing | None] | None
    annotations: list[Annotation | None] | None
    pid: strawberry.ID
    schema_type: str | None

