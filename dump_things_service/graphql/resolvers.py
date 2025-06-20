from __future__ import annotations

import types
from typing import (
    Any,
    Iterable,
)

import strawberry

from dump_things_service import JSON
from dump_things_service.model import get_subclasses
from dump_things_service.record import RecordDirStore
from dump_things_service.resolve_curie import resolve_curie


def get_all_records(
    strawberry_module: types.ModuleType,
    dir_store: RecordDirStore
) -> Iterable[Any]:
    """
    Resolver to get all records.
    """
    # TODO: this needs a new method in record dir store
    yield from get_records_by_class_name(
        strawberry_module,
        dir_store,
        'Thing'
    )


def get_record_by_pid(
    strawberry_module: types.ModuleType,
    dir_store: RecordDirStore,
    pid: strawberry.ID,
) -> Any | None:
    """
    Resolver to get a record by its PID.
    """
    iri = resolve_curie(dir_store.model, pid)
    class_name, record = dir_store.get_record_by_iri(iri)
    if class_name and record:
        inlined_record = _inline_relations(strawberry_module, dir_store, record)
        return getattr(strawberry_module, class_name)(**inlined_record)
    return None


def get_records_by_class_name(
    strawberry_module: types.ModuleType,
    dir_store: RecordDirStore,
    class_name: str
) -> Iterable[Any]:
    """
    Resolver to get records by class name.
    """
    for subclass_name in get_subclasses(dir_store.model, class_name):
        for _, record in dir_store.get_records_of_class(subclass_name):
            if record:
                yield getattr(strawberry_module, subclass_name)(**record)


def _inline_relations(
        strawberry_module: types.ModuleType,
        dir_store: RecordDirStore,
        record: dict,
) -> Any:
    if not record.get('relations'):
        return record

    new_relations = []
    for pid in record['relations']:
        related_class_name, related_record = dir_store.get_record_by_iri(
            resolve_curie(dir_store.model, pid)
        )
        if not related_class_name or not related_record:
            msg = f"Related record not found for PID: {pid}"
            raise ValueError(msg)

        new_relations.append(
            getattr(strawberry_module, related_class_name)(
                **_inline_relations(
                    strawberry_module,
                    dir_store,
                    related_record
                )
            )
        )
    record['relations'] = new_relations
    return record
