from __future__ import annotations

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
from dump_things_service.utils import cleaned_json

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path
    from typing import (
        Any,
    )

    from pydantic import BaseModel


ignored_files = {'.', '..', config_file_name}


submitter_class = 'NCIT_C54269'
submitter_class_base = 'http://purl.obolibrary.org/obo/'


class RecordDirStore:
    """Store records in a directory structure"""

    def __init__(
        self,
        root: Path,
        model: Any,
        pid_mapping_function: Callable,
    ):
        if not root.is_absolute():
            msg = f'Store root is not absolute: {root}'
            raise ValueError(msg)
        self.root = root
        self.model = model
        self.pid_mapping_function = pid_mapping_function

    def store_record(
        self,
        record: BaseModel,
        submitter_id: str,
        model: Any,
    ) -> Iterable[BaseModel]:
        final_records = self.extract_inlined(record, submitter_id)
        for final_record in final_records:
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
    ):
        # Generate the class directory
        class_name = record.__class__.__name__
        record_root = self.root / class_name
        record_root.mkdir(exist_ok=True)

        # Remember the submitter id
        self.annotate(record, submitter_id, model)

        # Convert the record object into a YAML object
        data = yaml.dump(
            # Remove the `schema_type` entry from the record. It does not belong
            # to the declared classes.
            data=cleaned_json(
                record.model_dump(exclude_none=True, mode='json'),
                remove_keys=('schema_type',),
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

    def get_record_by_pid(
        self,
        pid: str,
    ) -> tuple[str, JSON] | tuple[None, None]:
        for path in self.root.rglob('*'):
            if path.is_file() and path.name not in ignored_files:
                record = yaml.load(path.read_text(), Loader=yaml.SafeLoader)
                if record['pid'] == pid:
                    class_name = self._get_class_from_path(path)
                    return class_name, record
        return None, None

    def _get_class_from_path(self, path: Path) -> str:
        rel_path = path.absolute().relative_to(self.root)
        return rel_path.parts[0]

    def get_records_of_class(self, class_name: str) -> Iterable[tuple[str, JSON]]:
        for path in (self.root / class_name).rglob('*'):
            if path.is_file() and path.name not in ignored_files:
                class_name = self._get_class_from_path(path)
                yield (
                    class_name,
                    yaml.load(path.read_text(), Loader=yaml.SafeLoader),
                )
