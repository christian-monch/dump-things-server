"""
This is a proxy-backend that implements special handling for `schema_type` attributes.

It is mainly used as a layer on top of the `RecordDirBackend`. Because
`RecordDirBackend`s encode the class of the stored record in the record-path,
the `schema_type` attribute in the top level dictionary is redundant. Some
people prefer disk representation of records without the `schema_type` attribute.

This layer removes the attribute before the record is stored in the underlying
backend, i.e., it is not stored in the stored YAML files.

When a record is read from the backend, the `schema_type` attribute is added in
all cases (because we don't keep track of whether the initial record had a
`schema_type`-attribute or not). So every record read from this backend
will contain a `schema_type` attribute.
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
)

from dump_things_service.backends import (
    BackendResultList,
    RecordInfo,
    StorageBackend,
)
from dump_things_service.model import get_schema_model_for_schema

if TYPE_CHECKING:
    from types import ModuleType


__all__ = [
    'SchemaTypeLayer',
]


class SchemaTypeLayerResultList(BackendResultList):
    def __init__(
        self,
        origin_list: BackendResultList,
        schema_model: ModuleType,
    ):
        super().__init__()
        self.schema_model = schema_model
        self.origin_list = origin_list
        self.list_info = self.origin_list.list_info

    def generate_result(
        self,
        index: int,
        iri: str,
        class_name: str,
        sort_key: str,
        private: Any,
    ) -> RecordInfo:
        origin_element = self.origin_list.generate_result(
            index, iri, class_name, sort_key, private
        )
        if 'schema_type' not in origin_element.json_object:
            origin_element.json_object['schema_type'] = _get_schema_type(
                class_name,
                self.schema_model,
            )
        return origin_element


class _SchemaTypeLayer(StorageBackend):
    """Proxy backend that removes `schema_type` from stored records"""

    def __init__(
        self,
        backend: StorageBackend,
        schema: str,
    ):
        super().__init__()
        self.backend = backend
        self.schema_model = get_schema_model_for_schema(schema)

    def add_record(
        self,
        iri: str,
        class_name: str,
        json_object: dict,
    ):
        # Remove the top level `schema_type` from the JSON object because we
        # don't want to store it in the files. We add `schema_type` after
        # reading the record from disk. The value of `schema_type` is determined
        # by the class name of the record, which is stored in the path.
        if 'schema_type' in json_object:
            del json_object['schema_type']
        self.backend.add_record(
            iri=iri,
            class_name=class_name,
            json_object=json_object,
        )

    def get_record_by_iri(
        self,
        iri: str,
    ) -> RecordInfo | None:
        origin_result = self.backend.get_record_by_iri(iri)
        if origin_result and 'schema_type' not in origin_result.json_object:
            origin_result.json_object['schema_type'] = _get_schema_type(
                origin_result.class_name,
                self.schema_model,
            )
        return origin_result

    def get_records_of_classes(
        self,
        class_names: list[str],
        matching: str | None = None,
    ) -> BackendResultList:
        return SchemaTypeLayerResultList(
            origin_list=self.backend.get_records_of_classes(
                class_names,
                matching,
            ),
            schema_model=self.schema_model,
        )

    def get_all_records(
        self,
    ) -> BackendResultList:
        return SchemaTypeLayerResultList(
            origin_list=self.backend.get_all_records(),
            schema_model=self.schema_model,
        )

    def __getattr__(self, name: str) -> Any:
        """Delegate all other attributes to the underlying backend."""
        return getattr(self.backend, name)


def _get_schema_type(
    class_name: str,
    schema_module: ModuleType,
) -> str:
    return getattr(schema_module, class_name).class_class_curie


# Ensure that there is only one store per root directory.
_existing_layers = {}


def SchemaTypeLayer(  # noqa: N802
    backend: StorageBackend,
    schema: str,
) -> _SchemaTypeLayer:
    existing_layer, _ = _existing_layers.get(id(backend), (None, None))
    if not existing_layer:
        existing_layer = _SchemaTypeLayer(backend, schema)
        _existing_layers[id(backend)] = (existing_layer, backend)
    return existing_layer
