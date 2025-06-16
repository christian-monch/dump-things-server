from __future__ import annotations

from typing import Annotated, Union

import strawberry
from strawberry.schema.config import StrawberryConfig


def generic_resolver(pid_or_class, *args, **kwargs):
    """
    A generic resolver that returns the first argument.
    This is a placeholder and should be replaced with actual logic.
    """

    if pid_or_class == 'pid':
        return Person(given_name='hans', pid='1234', schema_type='Person')
    klass = globals()[pid_or_class]
    return [klass(pid=f'auto-{i}-{pid_or_class}') for i in range(1, 200)]

AllThings = Union['Agent', 'Annotation', 'InstantaneousEvent', 'Person', 'Thing']


@strawberry.type
class Agent:
    pid: str
    relations: list[Records | None] | None = None
    annotations: list[Annotation | None] | None = None
    schema_type: str | None = None
    acted_on_behalf_of: list[str | None] | None = None

@strawberry.type
class Annotation:
    annotation_tag: Thing = None
    annotation_value: str | None = None

@strawberry.type
class InstantaneousEvent:
    pid: str
    relations: list[Records | None] | None = None
    annotations: list[Annotation | None] | None = None
    schema_type: str | None = None
    at_time: str | None = None

@strawberry.type
class Person:
    pid: str
    relations: list[Records | None] | None = None
    annotations: list[Annotation | None] | None = None
    schema_type: str | None = None
    acted_on_behalf_of: list[str | None] | None = None
    given_name: str | None = None

@strawberry.type
class Thing:
    pid: str
    relations: list[Records | None] | None = None
    annotations: list[Annotation | None] | None = None
    schema_type: str | None = None


Records = Annotated[Agent | InstantaneousEvent | Person | Annotation | Thing, strawberry.union(name="Records")]


def resolve_all() -> list[Records] | None:
    """
    Resolve all objects of type Agent, Annotation, InstantaneousEvent, Person, and Thing.
    This is a placeholder and should be replaced with actual logic.
    """
    return [
        Agent(pid='auto-567-Agent'),
        Annotation(annotation_tag=Thing(pid='auto-567-Thing')),
        InstantaneousEvent(pid='auto-567-InstantaneousEvent'),
        Thing(pid='auto-567-Thing'),
        Person(pid='auto-567-Person', given_name='hans'),
    ]

def resolve_pid(pid: str) -> Agent | Annotation | InstantaneousEvent | Person | Thing | None:
    """
    Resolve a PID to the corresponding object.
    This is a placeholder and should be replaced with actual logic.
    """
    return Person(given_name=f'hans-{pid}', pid=pid)

def resolve_agents() -> list[Agent | None]:
    """
    Resolve all agents.
    This is a placeholder and should be replaced with actual logic.
    """
    return generic_resolver('Agent')

def resolve_annotations() -> list[Annotation | None]:
    """
    Resolve all annotations.
    This is a placeholder and should be replaced with actual logic.
    """
    return generic_resolver('Annotation')

def resolve_instantaneous_events() -> list[InstantaneousEvent | None]:
    """
    Resolve all instantaneous events.
    This is a placeholder and should be replaced with actual logic.
    """
    return generic_resolver('InstantaneousEvent')

def resolve_persons() -> list[Person | None]:
    """
    Resolve all persons.
    This is a placeholder and should be replaced with actual logic.
    """
    return [
        Person(pid='auto-567-Person', given_name='hans', relations=[
            Person(
                pid=f'sibling-{i}',
                given_name=f'sibling #{i}',
                relations=[Person(pid=f'grandson-{i}.{j}', given_name=f'grandon-{i}.{j}') for j in range(3)],
            ) for i in range(10)
        ]),
    ]
    return generic_resolver('Person')

def resolve_things() -> list[Thing | None]:
    """
    Resolve all things.
    This is a placeholder and should be replaced with actual logic.
    """
    return generic_resolver('Thing')


@strawberry.type
class Query:
    #@strawberry.field
    #def record(self, pid: str) -> Records | None:
    #    return resolve_pid(pid)
    record: Records | None = strawberry.field(resolver=resolve_pid)

    all: list[Records] | None = strawberry.field(resolver=resolve_all)

    pid: Agent | Annotation | InstantaneousEvent | Person | Thing | None = strawberry.field(resolver=resolve_pid)
    agents: list[Agent | None] | None = strawberry.field(resolver=resolve_agents)
    annotations: list[Annotation | None] | None = strawberry.field(resolver=resolve_annotations)
    instantaneous_events: list[InstantaneousEvent | None] | None = strawberry.field(resolver=resolve_instantaneous_events)
    persons: list[Person | None] | None = strawberry.field(resolver=resolve_persons)
    things: list[Thing | None] | None = strawberry.field(resolver=resolve_things)


schema = strawberry.Schema(
    query=Query,
    config=StrawberryConfig(auto_camel_case=False)
)

print(schema)
