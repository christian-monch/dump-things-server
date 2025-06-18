from __future__ import annotations

import types
from typing import Any

import strawberry

from dump_things_service.record import RecordDirStore
from dump_thing_service_graphql_strawberry_module import AllThings, AllRecords, ClassNames


def get_all_records(module: types.ModuleType) -> list[Any]:
    """
    Resolver to get all records.
    """
    return [
        module.Agent(pid=strawberry.ID('agent-1'), at_location='Berlin'),
        module.Person(pid=strawberry.ID('person-1'), given_name='John'),
        module.Thing(pid=strawberry.ID('thing-1'), description='A sample thing'),
    ]


def get_record_by_pid(
    module: types.ModuleType,
    pid: strawberry.ID,
) -> Any | None:
    """
    Resolver to get a record by its PID.
    """

    if pid.lower().startswith('person'):
        return module.Person(
            pid=strawberry.ID(pid),
            given_name=f'John-{{pid}}',
        )
    elif pid.lower().startswith('agent'):
        return module.Agent(
            pid=strawberry.ID(pid),
            at_location=f'Berlin-{{pid}}',
        )
    else:
        return module.Thing(
            pid=strawberry.ID(pid),
            description=f'Thing description for {{pid}}',
        )


def get_records_by_class_name(
    module: types.ModuleType,
    class_name: str
) -> list[Any] | None:
    """
    Resolver to get records by class name.
    """
    return [
        module.Agent(pid=strawberry.ID('agent-1'), at_location=f'Berlin {{class_name}}'),
        module.Agent(pid=strawberry.ID('agent-2'), at_location=f'Berlin {{class_name}}'),
        module.Agent(pid=strawberry.ID('agent-3'), at_location=f'Berlin {{class_name}}'),
    ]
