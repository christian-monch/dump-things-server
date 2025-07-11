"""
Backend that stores records in a directory structure

The disk-layout is described in <https://concepts.datalad.org/dump-things/>.
"""
from __future__ import annotations

import logging
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
from dump_things_service.model import get_model_for_schema
from dump_things_service.resolve_curie import resolve_curie

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path
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
        self.index = {}

    def build_index(
        self,
        schema: str,
    ):
        lgr.info('Building IRI index for records in %s', self.root)

        model = get_model_for_schema(schema)[0]

        self.index = {}
        for path in self.root.rglob(f'*.{self.suffix}'):
            if path.is_file() and path.name not in ignored_files:
                try:
                    # Catch YAML structure and payload errors
                    record = yaml.load(path.read_text(), Loader=yaml.SafeLoader)
                    pid = record['pid']
                except Exception as e:  # noqa: BLE001
                    lgr.error('Error: reading PID from record at %s: %s', path, e)
                    continue

                iri = resolve_curie(model, pid)
                sort_string = create_sort_key(record, self.order_by)
                self.index[iri] = self._get_class_name(path), path, sort_string

        lgr.info('Index built with %d IRIs', len(self.index))

    def _add_iri_to_index(
        self,
        iri: str,
        new_class: str,
        path: Path,
        sort_string: str,
    ):
        # If the IRI is already in the index, the reasons may be:
        #
        # 1. The existing record is updated. In this case the path should
        #    be the same as the one already in the index (which means the classes
        #    are the same and the PIDs are the same). No need to replace the path
        #    since they are identical anyway.
        # 2. The existing record is a different class (not `Thing`) and probably
        #    a different PID. That indicates that two different records have the
        #    same IRI. This is an error condition, and we raise an exception
        existing_entry = self.index.get(iri)
        if existing_entry:
            existing_class, existing_path, existing_sort_string = existing_entry
            # Case 1: existing record is updated
            if path == existing_path:
                self.index[iri] = existing_class, path, sort_string
                return
            # Case 2:
            msg = f'Duplicated IRI ({iri}): already indexed {existing_class}-instance at {existing_path} has the same IRI as new {new_class}-instance at {path}.'
            raise ValueError(msg)
        self.index[iri] = new_class, path, sort_string

    def _get_class_name(self, path: Path) -> str:
        """Get the class name from the path."""
        rel_path = path.absolute().relative_to(self.root)
        return rel_path.parts[0]

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

        # Remove the top level `schema_type` from the JSON object because we
        # don't want to store it in the YAML file. We add `schema_type` after
        # reading the record from disk. The value of `schema_type` is determined
        # by the class name of the record, which is stored in the path.
        if 'schema_type' in json_object:
            del json_object['schema_type']

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
        self._add_iri_to_index(iri, class_name, storage_path, sort_string)

    def get_record_by_iri(
        self,
        iri: str,
    ) -> RecordInfo | None:

        index_entry = self.index.get(iri)
        if index_entry is None:
            return None

        class_name, path, sort_key = index_entry
        json_object = yaml.load(path.read_text(), Loader=yaml.SafeLoader)
        return RecordInfo(
            iri=iri,
            class_name=class_name,
            json_object=json_object,
            sort_key=sort_key,
        )

    def get_records_of_classes(
        self,
        class_names: list[str]
    ) -> RecordDirResultList:

        return RecordDirResultList().add_info(
            sorted(
                (
                    ResultListInfo(
                        iri=iri,
                        class_name=class_name,
                        sort_key=sort_key,
                        private=path,
                    )
                    for iri, (class_name, path, sort_key) in self.index.items()
                    if class_name in class_names
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
