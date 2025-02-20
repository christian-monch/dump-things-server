"""Interface for storage backends.

A storage backend is an entity the knows different collections by name.
A collection stores records with unique identifiers (unique inside the
collection). All records of a collection have to conform to a schema, here
they are represented by Pydantic models.

A storage backend manages authorization keys. An authorization key allows
write- and read-access to an authorization-key specific extension of the
collections. Note: a valid authorization key can store records in every
collection.

"""
from __future__ import annotations

from abc import (
    ABCMeta,
    abstractmethod,
)
from typing import (
    Any,
    Iterable,
)

from pydantic import BaseModel

from dump_things_service.model import (
    build_model,
    get_classes,
    get_subclasses,
)


class StorageError(Exception):
    pass


class UnknownCollectionError(StorageError):
    pass


class UnknownClassError(StorageError):
    pass


class AuthorizationError(StorageError):
    pass


class CollectionInfo:
    def __init__(self, schema_location: str):
        self.schema_location = schema_location
        self.model, self.classes = self._create_model(schema_location)

    @staticmethod
    def _create_model(schema_location: str) -> tuple[Any, dict[str, Iterable[str]]]:
        model = build_model(schema_location)
        return (
            model,
            {
                class_name: get_subclasses(model, class_name)
                for class_name in get_classes(model)
            }
        )


class StorageBackendInterface(metaclass=ABCMeta):
    def __init__(self):
        self.collections = {}

    @abstractmethod
    def store(self,
        collection: str,
        record: BaseModel,
        authorization_info: Any,
    ):
        raise NotImplementedError('subclass responsibility')

    @abstractmethod
    def record_with_id(
        self,
        collection: str,
        identifier: str,
        authorization_info: Any | None = None,
    ) -> BaseModel | None:
        """Return classname and record data for the given identifier."""
        raise NotImplementedError

    @abstractmethod
    def records_of_class(
        self,
        collection: str,
        class_name: str,
        authorization_info: Any | None = None
    ) -> Iterable[BaseModel]:
        """Return classname and record data for all instances of class or it subclass."""
        raise NotImplementedError
