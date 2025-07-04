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

if TYPE_CHECKING:
    from collections.abc import Iterable

    from dump_things_service.lazy_list import LazyList


@dataclass
class RecordInfo:
    iri: str
    class_name: str
    json_object: dict[str, Any]
    # We store a sort key to support sorting of records from multiple, probably
    # sorted, sources.
    sort_key: str


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
    ) -> LazyList[RecordInfo]:
        raise NotImplementedError


def create_sort_key(
    json_object: dict[str, Any],
    order_by: Iterable[str],
) -> str:
    return '-'.join(
        str(json_object.get(key))
        if json_object.get(key) is not None
        else chr(0x10FFFF)
        for key in order_by
    )
