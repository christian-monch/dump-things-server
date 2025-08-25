"""
Base class for storage backends

Storage backends return multiple records as `LazyList[RecordInfo]` objects.
The reason for using a lazy list instead of yielding records one by one is that
fastapi endpoints and fastapi-pagination work with list like objects and not
with generators, i.e. it uses index- or slice-based access to the records.
"""

from __future__ import annotations

from abc import (
    ABCMeta,
    abstractmethod,
)
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
)

from dump_things_service.lazy_list import LazyList

if TYPE_CHECKING:
    from collections.abc import Iterable


@dataclass
class RecordInfo:
    iri: str
    class_name: str
    json_object: dict[str, Any]
    # We store a sort key to support sorting of records from multiple, probably
    # sorted, sources.
    sort_key: str


@dataclass
class ResultListInfo:
    iri: str
    class_name: str
    sort_key: str
    private: Any


class BackendResultList(LazyList):
    """
    Implementation of a lazy list that holds references to records stored in
    a backend. The list elements carry a sort key that allows sorting of the
    list. The lazy list-approach is used for the results of
    `get_records_of_classes`, which can be large, i.e. in the millions, because:

    1. Fastapi pagination requires a list-like object that can be sliced and
       indexed. Lazy lists allow us to keep only objects of the current slice
       in memory.

    2. The service integrates elements from multiple backends; this requires
       a possibility to sort the results from different backends into an
       integrated result. The `sort_key` supports this by providing a
       backend-independent, record-specific key that can be used to sort the
       records.
    """

    def generate_element(self, index: int, info: ResultListInfo) -> RecordInfo:
        """
        Generate a JSON representation of the record at index `index`.

        :param index: The index of the record that should be retrieved (ignored).
        :param info: The tuple (iri, record_class_name, record_path).
        :return: A JSON object.
        """
        return self.generate_result(
            index, info.iri, info.class_name, info.sort_key, info.private
        )

    def unique_identifier(self, info: ResultListInfo) -> Any:
        # Return the IRI as unique identifier
        return info.iri

    def sort_key(self, info: ResultListInfo) -> str:
        # Return the sort_key entry as sort key
        return info.sort_key

    @abstractmethod
    def generate_result(
        self,
        index: int,
        iri: str,
        class_name: str,
        sort_key: str,
        private: Any,
    ) -> RecordInfo:
        """
        Generate a record info object from the provided parameters.

        :param index: The index of the record.
        :param iri: The IRI of the record.
        :param class_name: The class name of the record.
        :param sort_key: The sort key for the record.
        :param private: Additional private information, if any.
        :return: A RecordInfo object.
        """
        raise NotImplementedError


class StorageBackend(metaclass=ABCMeta):
    def __init__(
        self,
        order_by: Iterable[str] | None = None,
    ):
        self.order_by = order_by or ['pid']

    @abstractmethod
    def add_record(
        self,
        iri: str,
        class_name: str,
        json_object: dict,
    ):
        raise NotImplementedError

    def add_records_bulk(
        self,
        object_info: Iterable[RecordInfo],
    ):
        """Default implementation for adding multiple records at once."""
        for info in object_info:
            self.add_record(
                iri=info.iri,
                class_name=info.class_name,
                json_object=info.json_object,
            )

    @abstractmethod
    def get_record_by_iri(
        self,
        iri: str,
    ) -> RecordInfo | None:
        raise NotImplementedError

    @abstractmethod
    def get_records_of_classes(
        self,
        class_names: Iterable[str],
        matching: str | None = None,
    ) -> BackendResultList:
        raise NotImplementedError

    @abstractmethod
    def get_all_records(
        self,
    ) -> BackendResultList:
        raise NotImplementedError


def create_sort_key(
    json_object: dict[str, Any],
    order_by: Iterable[str],
) -> str:
    return '-'.join(
        str(json_object.get(key)) if json_object.get(key) is not None else chr(0x10FFFF)
        for key in order_by
    )
