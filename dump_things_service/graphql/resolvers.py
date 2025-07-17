from __future__ import annotations

import types
from typing import (
    TYPE_CHECKING,
    Any,
    Iterable,
)

import strawberry

from dump_things_service.common import get_permissions
from dump_things_service.config import get_model_info_for_collection
from dump_things_service.model import get_subclasses
from dump_things_service.resolve_curie import resolve_curie

if TYPE_CHECKING:
    from dump_things_service.config import InstanceConfig


def get_all_records(
    instance_config: InstanceConfig,
    collection: str,
    strawberry_module: types.ModuleType,
    context,
) -> Iterable:
    """
    Resolver to get all records.
    """
    # TODO: this needs a new method in record dir store
    yield from get_records_by_class_name(
        instance_config,
        collection,
        strawberry_module,
        'Thing',
        context,
    )


def get_record_by_pid(
    instance_config: InstanceConfig,
    collection: str,
    strawberry_module: types.ModuleType,
    pid: strawberry.ID,
    context,
) -> Any | None:
    """
    Resolver to get a record by its PID.
    """
    final_permissions, token_store, _ = get_permissions(
        instance_config,
        context.token,
        collection,
    )

    iri = resolve_curie(
        get_model_info_for_collection(instance_config, collection)[0],
        pid,
    )

    class_name = None
    record = None
    if final_permissions.incoming_read:
        class_name, record = token_store.get_object_by_iri(iri)

    if not record and final_permissions.curated_read:
        class_name, record = instance_config.curated_stores[collection].get_object_by_iri(iri)

    if class_name and record:
        _convert_relations(record)
        return getattr(strawberry_module, class_name)(**record)
    return None


def get_records_by_class_name(
    instance_config: InstanceConfig,
    collection: str,
    strawberry_module: types.ModuleType,
    class_name: str,
    context,
) -> Iterable:
    """
    Resolver to get records by class name.
    """
    final_permissions, token_store, _ = get_permissions(
        instance_config,
        context.token,
        collection,
    )

    records = {}
    if final_permissions.curated_read:
        for search_class_name in get_subclasses(instance_config.curated_stores[collection].model, class_name):
            for record_info in instance_config.curated_stores[collection].get_objects_of_class(
                    search_class_name
            ):
                record_class_name = record_info.class_name
                record = record_info.json_object
                records[record['pid']] = record_class_name, record

    if final_permissions.incoming_read:
        for search_class_name in get_subclasses(token_store.model, class_name):
            for record_info in token_store.get_objects_of_class(search_class_name):
                record_class_name = record_info.class_name
                record = record_info.json_object
                records[record['pid']] = record_class_name, record

    for pid, (record_class_name, record) in records.items():
        _convert_relations(record)
        yield getattr(strawberry_module, record_class_name)(**record)


def _convert_relations(
    record: dict,
) -> None:
    if record.get('relations'):
        record['relations'] = list(record['relations'])
