from __future__ import annotations

import sys
import types
from typing import (
    Any,
    cast,
)

import strawberry

strawberry_module = sys.modules['dump_thing_service_graphql_strawberry_module']
from dump_things_service.record import RecordDirStore

AllThings = strawberry_module.AllThings
AllRecords = strawberry_module.AllRecords
ClassNames = strawberry_module.ClassNames



#def get_all_records(module: types.ModuleType) -> list[Any]:
def get_all_records(dir_store: RecordDirStore) -> list[AllRecords]:
    """
    Resolver to get all records.
    """
    # TODO: this needs a new method in record dir store
    return [
        getattr(strawberry_module, class_name)(**record)
        for class_name, record in dir_store.get_records_of_class('Thing')
        if class_name and record
    ]

def get_record_by_pid(
    dir_store: RecordDirStore,
    pid: strawberry.ID,
) -> AllThings | None:
    """
    Resolver to get a record by its PID.
    """
    class_name, record = dir_store.get_record_by_iri(pid)
    if class_name and record:
        return getattr(strawberry_module, class_name)(**record)
    return None


def get_records_by_class_name(
    dir_store: RecordDirStore,
    class_name: str
) -> list[AllThings] | None:
    """
    Resolver to get records by class name.
    """
    return [
        getattr(strawberry_module, class_name)(**record)
        for class_name, record in dir_store.get_records_of_class(class_name)
        if class_name and record
    ]
