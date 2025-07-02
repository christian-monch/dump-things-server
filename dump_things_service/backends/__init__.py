"""
Base class for storage backends
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
    def get_records_of_class(
        self,
        class_name: str,
    ) -> LazyList[RecordInfo]:
        raise NotImplementedError
