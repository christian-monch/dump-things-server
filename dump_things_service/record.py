from __future__ import annotations

import logging
from itertools import chain
from typing import (
    TYPE_CHECKING,
    Callable,
)

import yaml
from fastapi import HTTPException

from dump_things_service import (
    HTTP_400_BAD_REQUEST,
    JSON,
    config_file_name,
)
from dump_things_service.resolve_curie import resolve_curie
from dump_things_service.utils import cleaned_json

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path
    from typing import (
        Any,
    )

    from pydantic import BaseModel

    from dump_things_service.config import InstanceConfig


ignored_files = {'.', '..', config_file_name}

lgr = logging.getLogger('dump_things_service')

submitter_class = 'NCIT_C54269'
submitter_class_base = 'http://purl.obolibrary.org/obo/'


class RecordDirStore:
    """Store records in a directory structure"""

    def __init__(
        self,
        root: Path,
        model: Any,
        pid_mapping_function: Callable,
        suffix: str,
    ):
        if not root.is_absolute():
            msg = f'Store root is not absolute: {root}'
            raise ValueError(msg)
        self.root = root
        self.model = model
        self.pid_mapping_function = pid_mapping_function
        self.suffix = suffix
        self.index = {}
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
                    pid = record['pid']
                except Exception:   # noqa: BLE001
                    lgr.error('Error: record at %s does not contain a mapping with `pid`', path)
                    continue

                iri = resolve_curie(self.model, pid)
                # On startup, log PID collision errors and continue building the index
                try:
                    self._add_iri_to_index(iri, path)
                except HTTPException as e:
                    lgr.error(e.detail)
        lgr.info('Index built with %d IRIs', len(self.index))

    def _add_iri_to_index(self, iri: str, path: Path):

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
        existing_path = self.index.get(iri)
        if existing_path:
            # Case 1: existing record is updated
            if path == existing_path:
                return

            existing_class = self._get_class_name(existing_path)
            new_class = self._get_class_name(path)

            # Case 2: `Thing` record is replaced with a non-`Thing` record.
            if existing_class == 'Thing' and new_class != 'Thing':
                if path.name == existing_path.name:
                    self.index[iri] = path
                    return
                msg = f'IRI {iri} existing {existing_class}-instance at {existing_path} might not be a placeholder for {new_class}-instance at {path}, PIDs differ!'
                raise HTTPException(
                    HTTP_400_BAD_REQUEST,
                    detail=msg,
                )

            # Case 3: a placeholder `Thing` should be added.
            if existing_class != 'Thing' and new_class == 'Thing':
                if path.name == existing_path.name:
                    # The `Thing` record is just a placeholder, we can ignore it
                    return
                msg = f'IRI {iri} existing {existing_class}-instance at {existing_path} must not be replace by {new_class}-instance at {path}. PIDs differ!'
                raise HTTPException(
                    HTTP_400_BAD_REQUEST,
                    detail=msg,
                )

            # Case 4:
            msg = f'Duplicated IRI ({iri}): already index {existing_class}-instance at {existing_path} has the same IRI as new {new_class}-instance at {path}.'
            raise HTTPException(
                HTTP_400_BAD_REQUEST,
                detail=msg,
            )

        self.index[iri] = path

    def _get_class_name(self, path: Path) -> str:
        """Get the class name from the path."""
        rel_path = path.absolute().relative_to(self.root)
        return rel_path.parts[0]

    def rebuild_index(self):
        self.index = {}
        self._build_index()

    def store_record(
        self,
        record: BaseModel,
        submitter_id: str,
        model: Any,
    ) -> Iterable[BaseModel]:
        final_records = self.extract_inlined(record, submitter_id)
        for final_record in final_records:
            if final_record is not None:
                yield self.store_single_record(
                    record=final_record,
                    submitter_id=submitter_id,
                    model=model,
                )

    def extract_inlined(
        self,
        record: BaseModel,
        submitter_id: str,
    ) -> list[BaseModel]:
        # The trivial case: no relations
        if not hasattr(record, 'relations') or record.relations is None:
            return [record]

        extracted_sub_records = list(
            chain(
                *[
                    self.extract_inlined(sub_record, submitter_id)
                    for sub_record in record.relations.values()
                    # Do not extract 'empty'-Thing records, those are just placeholders
                    if sub_record != self.model.Thing(pid=sub_record.pid)
                ]
            )
        )
        # Simplify the relations in this record
        new_record = record.model_copy()
        new_record.relations = {
            sub_record_pid: self.model.Thing(pid=sub_record_pid)
            for sub_record_pid in record.relations
        }
        return [new_record, *extracted_sub_records]

    def store_single_record(
        self,
        record: BaseModel,
        submitter_id: str,
        model: Any,
    ) -> BaseModel | None:
        # Generate the class directory
        class_name = record.__class__.__name__
        record_root = self.root / class_name
        record_root.mkdir(exist_ok=True)

        # Remember the submitter id
        self.annotate(record, submitter_id, model)

        # Convert the record object into a YAML object
        data = yaml.dump(
            # Remove the `schema_type` entry from the record. The type is
            # defined by the path under which the record is stored.
            data=cleaned_json(
                record.model_dump(exclude_none=True, mode='json'),
                remove_keys=('schema_type', '@type'),
            ),
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )

        # Apply the mapping function to the record pid to get the final storage path
        storage_path = record_root / self.pid_mapping_function(
            pid=record.pid, suffix='yaml'
        )

        # Ensure that the storage path is within the record root
        try:
            storage_path.relative_to(record_root)
        except ValueError as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST, detail='Invalid pid.'
            ) from e

        # Ensure all intermediate directories exist and save the YAML document
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        storage_path.write_text(data, encoding='utf-8')

        # Add the resolved PID to the index
        iri = resolve_curie(self.model, record.pid)
        self._add_iri_to_index(iri, storage_path)

        return record

    def annotate(
        self,
        record: BaseModel,
        submitter_id: str,
        model: Any,
    ) -> None:
        """Add submitter IRI to the record annotations, use CURI if possible"""
        submitter_iri = self.get_compact_iri(
            submitter_class_base,
            submitter_class,
            model,
        )
        if not record.annotations:
            record.annotations = {}
        record.annotations[submitter_iri] = submitter_id

    @staticmethod
    def get_compact_iri(iri: str, class_name: str, model: Any):
        prefixes = model.linkml_meta.root.get('prefixes')
        if prefixes:
            for prefix_info in prefixes.values():
                if prefix_info['prefix_reference'] == iri:
                    return f'{prefix_info["prefix_prefix"]}:{class_name}'
        return f'{iri}{class_name}'

    def get_record_by_iri(
        self,
        iri: str,
    ) -> tuple[str, JSON] | tuple[None, None]:
        path = self.index.get(iri)
        if path is None:
            return None, None
        record = yaml.load(path.read_text(), Loader=yaml.SafeLoader)
        class_name = self._get_class_name(path)
        return class_name, record

    def get_records_of_class(self, class_name: str) -> Iterable[tuple[str, JSON]]:
        for path in self.index.values():
            path_class_name = self._get_class_name(path)
            if class_name == path_class_name:
                yield (
                    class_name,
                    yaml.load(path.read_text(), Loader=yaml.SafeLoader),
                )


def get_record_dir_store(
        instance_config: InstanceConfig,
        root: Path,
        model: Any,
        pid_mapping_function: Callable,
        suffix: str,
) -> RecordDirStore:
    """Get a record directory store for the given root directory."""
    existing_store = instance_config.stores.get(root)
    if not existing_store:
        existing_store = RecordDirStore(
            root=root,
            model=model,
            pid_mapping_function=pid_mapping_function,
            suffix=suffix,
        )
        instance_config.stores[root] = existing_store

    if existing_store.model != model:
        msg = f'Store at {root} already exists with different model.'
        raise ValueError(msg)

    if existing_store.pid_mapping_function != pid_mapping_function:
        msg = f'Store at {root} already exists with different PID mapping function.'
        raise ValueError(msg)

    if existing_store.suffix != suffix:
        msg = f'Store at {root} already exists with different format.'
        raise ValueError(msg)

    return existing_store
