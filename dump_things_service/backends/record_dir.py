"""
Backend that stores records in a directory structure

The disk-layout is described in <https://concepts.datalad.org/dump-things/>.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Callable,
)

import yaml

from dump_things_service import config_file_name
from dump_things_service.backends import (
    BackendResultList,
    RecordInfo,
    ResultListInfo,
    StorageBackend,
    create_sort_key,
)
from dump_things_service.backends.record_dir_index import RecordDirIndex

if TYPE_CHECKING:
    from collections.abc import Iterable
    from types import ModuleType


__all__ = [
    'RecordDirStore',
]

ignored_files = {'.', '..', config_file_name}

lgr = logging.getLogger('dump_things_service')


class RecordDirResultList(BackendResultList):
    """
    The specific result list for record directory backends.
    """

    def generate_result(
        self,
        _: int,
        iri: str,
        class_name: str,
        sort_key: str,
        path: Path,
    ) -> RecordInfo:
        """
        Generate a JSON representation of the record at index `index`.

        :param _: The index of the record.
        :param iri: The IRI of the record.
        :param class_name: The class name of the record.
        :param sort_key: The sort key for the record.
        :param path: The path where the record is stored
        :return: A RecordInfo object.
        """
        with path.open('r') as f:
            json_object = yaml.load(f, Loader=yaml.SafeLoader)
            return RecordInfo(
                iri=iri,
                class_name=class_name,
                json_object=json_object,
                sort_key=sort_key,
            )


class _RecordDirStore(StorageBackend):
    """Store records in a directory structure"""

    def __init__(
        self,
        root: Path,
        pid_mapping_function: Callable,
        suffix: str,
        order_by: Iterable[str] | None = None,
    ):
        super().__init__(order_by=order_by)
        if not root.is_absolute():
            msg = f'Store root is not absolute: {root}'
            raise ValueError(msg)
        self.root = root
        self.pid_mapping_function = pid_mapping_function
        self.suffix = suffix
        self.index = RecordDirIndex(root, suffix)

    def build_index(
        self,
        schema: str,
    ):
        self.index.rebuild_index(schema, self.order_by)

    def build_index_if_needed(
        self,
        schema: str,
    ):
        self.index.rebuild_if_needed(schema, self.order_by)

    def add_record(
        self,
        iri: str,
        class_name: str,
        json_object: dict,
    ):
        pid = json_object['pid']

        # Generate the class directory, apply the mapping function to the record
        # pid to get the final storage path.
        record_root = self.root / class_name
        record_root.mkdir(exist_ok=True)
        storage_path = record_root / self.pid_mapping_function(pid=pid, suffix='yaml')

        # Ensure that the storage path is within the record root
        try:
            storage_path.relative_to(record_root)
        except ValueError as e:
            msg = (
                f'Invalid pid ({pid}) for mapping function: {self.pid_mapping_function}'
            )
            raise ValueError(msg) from e

        # Ensure all intermediate directories exist and save the YAML document
        storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert the record object into a YAML object
        data = yaml.dump(
            data=json_object,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )
        storage_path.write_text(data, encoding='utf-8')

        # Add the IRI to the index.
        sort_string = create_sort_key(json_object, self.order_by)
        self.index.add_iri_info(iri, class_name, str(storage_path), sort_string)

    def get_record_by_iri(
        self,
        iri: str,
    ) -> RecordInfo | None:
        index_entry = self.index.get_info_for_iri(iri)
        if index_entry is None:
            return None

        class_name, path, sort_key = index_entry
        json_object = yaml.load(Path(path).read_text(), Loader=yaml.SafeLoader)
        return RecordInfo(
            iri=iri,
            class_name=class_name,
            json_object=json_object,
            sort_key=sort_key,
        )

    def get_records_of_classes(
        self,
        class_names: list[str],
        matching: str | None = None,
    ) -> RecordDirResultList:
        return RecordDirResultList().add_info(
            sorted(
                (
                    ResultListInfo(
                        iri=index_entry.iri,
                        class_name=index_entry.class_name,
                        sort_key=index_entry.sort_key,
                        private=Path(index_entry.path),
                    )
                    for class_name in class_names
                    for index_entry in self.index.get_info_for_class(class_name)
                ),
                key=lambda result_list_info: result_list_info.sort_key,
            )
        )

    def get_all_records(
        self,
    ) -> RecordDirResultList:
        return RecordDirResultList().add_info(
            sorted(
                (
                    ResultListInfo(
                        iri=index_entry.iri,
                        class_name=index_entry.class_name,
                        sort_key=index_entry.sort_key,
                        private=Path(index_entry.path),
                    )
                    for index_entry in self.index.get_info_for_all_classes()
                ),
                key=lambda result_list_info: result_list_info.sort_key,
            )
        )


# Ensure that there is only one store per root directory.
_existing_stores = {}


def RecordDirStore(  # noqa: N802
    root: Path,
    pid_mapping_function: Callable,
    suffix: str,
    order_by: Iterable[str] | None = None,
) -> _RecordDirStore:
    """Get a record directory store for the given root directory."""
    existing_store = _existing_stores.get(root)
    if not existing_store:
        existing_store = _RecordDirStore(
            root=root,
            pid_mapping_function=pid_mapping_function,
            suffix=suffix,
            order_by=order_by,
        )
        _existing_stores[root] = existing_store

    if existing_store.pid_mapping_function != pid_mapping_function:
        msg = f'Store at {root} already exists with different PID mapping function.'
        raise ValueError(msg)

    if existing_store.suffix != suffix:
        msg = f'Store at {root} already exists with different format.'
        raise ValueError(msg)

    if existing_store.order_by != (order_by or ['pid']):
        msg = f'Store at {root} already exists with different order specification.'
        raise ValueError(msg)

    return existing_store


def _get_schema_type(
    class_name: str,
    schema_module: ModuleType,
) -> str:
    return getattr(schema_module, class_name).class_class_curie
