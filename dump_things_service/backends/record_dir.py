from __future__ import annotations

import logging
from typing import (
    TYPE_CHECKING,
    Callable,
)

import yaml

from dump_things_service import config_file_name
from dump_things_service.backends import (
    RecordInfo,
    StorageBackend,
)
from dump_things_service.lazy_list import LazyList
from dump_things_service.resolve_curie import resolve_curie

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any

    from dump_things_service.config import InstanceConfig


ignored_files = {'.', '..', config_file_name}

lgr = logging.getLogger('dump_things_service')

last_character = chr(0x10FFFF)


class RecordList(LazyList):
    """
    Implementation of a lazy list that holds records stored on disk. This is
    mainly used as array argument for `fastapi_pagination.paginate` to load
    only the records that are needed for the current page.
    """

    def __init__(
        self,
        instance_config: InstanceConfig | None = None,
        collection: str | None = None,
    ):
        super().__init__()
        self.instance_config = instance_config
        self.collection = collection

    def generate_element(self, _: int, info: Any) -> RecordInfo:
        """
        Generate a JSON representation of the record at index `index`.

        :param _: The index of the record to retrieve.
        :param info: The tuple (iri, record_class_name, record_path).
        :return: A JSON object.
        """
        with info[2].open('r') as f:
            return RecordInfo(
                iri=info[0],
                class_name=info[1],
                json_object=yaml.load(f, Loader=yaml.SafeLoader),
            )


class RecordDirStore(StorageBackend):
    """Store records in a directory structure"""

    def __init__(
        self,
        root: Path,
        model: Any,
        pid_mapping_function: Callable,
        suffix: str,
        sort_keys: list,
    ):
        super().__init__()
        if not root.is_absolute():
            msg = f'Store root is not absolute: {root}'
            raise ValueError(msg)
        self.root = root
        self.model = model
        self.pid_mapping_function = pid_mapping_function
        self.suffix = suffix
        self.index = {}
        self.sort_keys = sort_keys or ['pid']
        self._build_index()

    def _build_index(self):
        lgr.info('Building IRI index for records in %s', self.root)
        for path in self.root.rglob(f'*.{self.suffix}'):
            if path.is_file() and path.name not in ignored_files:
                try:
                    # Catch YAML structure errors
                    record = yaml.load(path.read_text(), Loader=yaml.SafeLoader)
                except Exception as e:  # noqa: BLE001
                    lgr.error('Error: reading YAML record from %s: %s', path, e)
                    continue

                try:
                    # Catch YAML payload errors
                    pid = record['pid']
                except (TypeError, KeyError):
                    lgr.error(
                        'Error: record at %s does not contain a mapping with `pid`',
                        path,
                    )
                    continue

                iri = resolve_curie(self.model, pid)
                sort_string = '-'.join(
                    str(record.get(key))
                    if record.get(key) is not None
                    else last_character
                    for key in self.sort_keys
                )

                # On startup, log PID collision errors and continue building the index
                try:
                    self._add_iri_to_index(
                        iri, self._get_class_name(path), pid, path, sort_string
                    )
                except ValueError as e:
                    lgr.error('Error during index creation: %s', e)
        lgr.info('Index built with %d IRIs', len(self.index))

    def _add_iri_to_index(
        self,
        iri: str,
        new_class: str,
        pid: str,
        path: Path,
        sort_string: str,
    ):
        # If the IRI is already in the index, the reasons may be:
        #
        # 1. The existing record is updated. In this case the path should
        #    be the same as the one already in the index (which means the classes
        #    are the same and the PIDs are the same). No need to replace the path
        #    since they are identical anyway.
        # 2. The existing record is a `Thing` record, and the new record is not a
        #    `Thing` record (visible by its `path`). The `Thing` record should
        #    just be a placeholder. The final path component should be identical
        #    (which means that both records have the same PID). In this case we
        #    replace the existing record with the new one. If the PIDs are different,
        #    we cannot be sure that the `Thing` record is just a placeholder, and
        #    we raise an exception.
        # 3. The existing record is not a `Thing` record, and the new record is a
        #    `Thing` record. If both have identical PIDs (final path component),
        #    we ignore the new record, since it is just a placeholder. If the PIDs
        #    differ, we raise an exception, since it indicates that two unrelated
        #    records have the same IRI, which is an error condition.
        # 4. The existing record is a different class (not `Thing`) and probably
        #    a different PID. That indicates that two different records have the
        #    same IRI. This is an error condition, and we raise an exception
        existing_entry = self.index.get(iri)
        if existing_entry:
            existing_class, existing_pid, existing_path, existing_sort_string = (
                existing_entry
            )
            # Case 1: existing record is updated
            if path == existing_path:
                self.index[iri] = existing_class, pid, path, sort_string
                return

            # Case 2: `Thing` record is replaced with a non-`Thing` record.
            if existing_class == 'Thing' and new_class != 'Thing':
                if path.name == existing_path.name:
                    self.index[iri] = new_class, pid, path, sort_string
                    return
                msg = f'IRI {iri} existing {existing_class}-instance at {existing_path} might not be a placeholder for {new_class}-instance at {path}, PIDs differ!'
                raise ValueError(msg)

            # Case 3: a placeholder `Thing` was handed in to be added.
            if existing_class != 'Thing' and new_class == 'Thing':
                if path.name == existing_path.name:
                    # The `Thing` record is just a placeholder, we can ignore it
                    return
                msg = f'IRI {iri} existing {existing_class}-instance at {existing_path} must not be replace by {new_class}-instance at {path}. PIDs differ!'
                raise ValueError(msg)

            # Case 4:
            msg = f'Duplicated IRI ({iri}): already indexed {existing_class}-instance at {existing_path} has the same IRI as new {new_class}-instance at {path}.'
            raise ValueError(msg)

        self.index[iri] = new_class, pid, path, sort_string

    def _get_class_name(self, path: Path) -> str:
        """Get the class name from the path."""
        rel_path = path.absolute().relative_to(self.root)
        return rel_path.parts[0]

    def rebuild_index(self):
        self.index = {}
        self._build_index()

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

        # Add the IRI to the index
        sort_string = '-'.join(
            getattr(json_object, key) if hasattr(json_object, key) else last_character
            for key in self.sort_keys
        )
        self._add_iri_to_index(iri, class_name, pid, storage_path, sort_string)

    def get_record_by_iri(
        self,
        iri: str,
    ) -> RecordInfo | None:
        class_name, pid, path, sort_key = self.index.get(iri)
        if path is None:
            return None
        record = yaml.load(path.read_text(), Loader=yaml.SafeLoader)
        return RecordInfo(iri=iri, class_name=class_name, json_object=record)

    def get_records_of_class(self, class_name: str) -> RecordList:
        return RecordList().add_info(
            sorted(
                (
                    (iri, index_entry[0], index_entry[2])
                    for iri, index_entry in self.index.items()
                    if index_entry[0] == class_name
                ),
                key=lambda index_entry: index_entry[3],
            )
        )
