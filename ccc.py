from __future__ import annotations

import strawberry
from enum import Enum
from typing import Annotated
from typing import NewType
from typing import Union

AllThings = Annotated[
    Union[
        'Thing',
        'Agent',
        'Person',
    ],
    strawberry.union(name="AllThings")
]


@strawberry.interface
class ThingMixin:
    annotations: list[str | None] | None = None
    broad_mappings: list[str | None] | None = None
    close_mappings: list[str | None] | None = None
    description: str | None = None
    exact_mappings: list[str | None] | None = None
    attributes: list[str | None] | None = None
    characterized_by: list[str | None] | None = None
    narrow_mappings: list[str | None] | None = None
    related_mappings: list[str | None] | None = None
    schema_type: str | None = None


@strawberry.type
class Thing(ThingMixin):
    pid: strawberry.ID = None
    relations: list[AllThings] | None = None


@strawberry.type
class Agent(Thing):
    acted_on_behalf_of: list[Agent | None] | None = None
    at_location: str | None = None
    identifiers: list[str | None] | None = None
    qualified_relations: list[str | None] | None = None



@strawberry.type
class Person(Agent):
    additional_names: list[str | None] | None = None
    family_name: str | None = None
    given_name: str | None = None
    honorific_name_prefix: str | None = None
    honorific_name_suffix: str | None = None
    formatted_name: str | None = None


@strawberry.enum
class ClassNames(Enum):
    Agent = "Agent"
    Person = "Person"
    Thing = "Thing"


def resolve_pid(pid: str) -> AllThings | None:
    if pid.lower().startswith('person'):
        return Person(
            pid=strawberry.ID(pid),
            given_name=f'John-{pid}',
        )
    elif pid.lower().startswith('agent'):
        return Agent(
            pid=strawberry.ID(pid),
            at_location=f'Berlin-{pid}',
        )
    else:
        return Thing(
            pid=strawberry.ID(pid),
            description=f'Thing description for {pid}',
        )


def resolve_all() -> list[AllThings] | None:
    return [
        Agent(pid=strawberry.ID('agent-1'), at_location='Berlin'),
        Person(pid=strawberry.ID('person-1'), given_name='John'),
        Thing(pid=strawberry.ID('thing-1'), description='A sample thing'),
    ]


def resolve_records(class_name: ClassNames) -> list[AllThings] | None:
    return [
        Agent(pid=strawberry.ID('agent-1'), at_location=f'Berlin {class_name}'),
        Agent(pid=strawberry.ID('agent-2'), at_location=f'Berlin {class_name}'),
        Agent(pid=strawberry.ID('agent-3'), at_location=f'Berlin {class_name}'),
    ]


@strawberry.type
class Query:
    record: AllThings | None = strawberry.field(resolver=resolve_pid)
    all: list[AllThings] = strawberry.field(resolver=resolve_all)
    records: list[AllThings] = strawberry.field(resolver=resolve_records)


schema = strawberry.Schema(query=Query)
