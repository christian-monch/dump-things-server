from __future__ import annotations

from pydantic import BaseModel

from dump_things_service.backends import (
    RecordInfo,
    StorageBackend,
)
from dump_things_service.lazy_list import LazyList
from dump_things_service.model import (
    get_subclasses,
    get_model_for_schema,
)
from dump_things_service.resolve_curie import resolve_curie


class ModelStore:
    def __init__(
        self,
        schema: str,
        backend: StorageBackend,
    ):
        self.schema = schema
        self.model = get_model_for_schema(self.schema)[0]
        self.backend = backend

    def store_object(
        self,
        obj: BaseModel,
    ) -> None:
        # TODO:
        #  - extract inlined records
        #  - add submitter information
        iri = resolve_curie(self.model, obj.pid)
        self.backend.add_record(
            iri,
            obj.__class__.__name__,
            obj.model_dump(mode='json', exclude_none=True),
        )

    def get_object_by_pid(
        self,
        pid: str,
    ) -> dict:
        return self.get_object_by_iri(resolve_curie(self.model, pid))

    def get_object_by_iri(
        self,
        iri: str,
    ) -> dict | None:
        record_info = self.backend.get_record_by_iri(iri)
        if record_info:
            return record_info.json_object
        return None

    def get_objects_of_class(
        self,
        class_name: str,
    ) -> LazyList[RecordInfo]:
        """
        Get all objects of a specific class.

        :param class_name: The name of the class to filter by.
        :return: A lazy list of objects of the specified class and its subclasses.
        """
        class_names = get_subclasses(self.model, class_name)
        return self.backend.get_records_of_classes(class_names)
