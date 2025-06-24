""" Implementation of a lazy list that holds records stored on disk.

This is mainly used as array argument for `fastapi_pagination.paginate` to
load only the records that are needed for the current page.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from dump_things_service.convert import convert_json_to_ttl
from dump_things_service.lazy_list import LazyList
from dump_things_service.utils import (
    cleaned_json,
    get_schema_type_curie,
)

if TYPE_CHECKING:
    from typing import Any

    from dump_things_service.config import InstanceConfig


class RecordList(LazyList):

    def __init__(
        self,
        instance_config: InstanceConfig | None = None,
        collection: str | None = None,
        *,
        convert_to_ttl: bool = False,
    ):
        super().__init__()
        self.instance_config = instance_config
        self.collection = collection
        self.convert_to_ttl = convert_to_ttl

    def generate_element(self, index: int, info: Any) -> str | dict:
        """
        Generate a JSON or TTL representation of the record at index `index`.

        :param index: The index of the record to retrieve.
        :param info: A tuple containing (record_class_name, record_pid,
        :return: A tuple containing (record_class_name, record_pid, record_path).
        """
        with info[2].open('r')  as f:
            record_content = yaml.load(f, Loader=yaml.SafeLoader)
            record_content['schema_type'] = get_schema_type_curie(
                self.instance_config,
                self.collection,
                info[0]
            )
            if self.convert_to_ttl:
                record_content = convert_json_to_ttl(
                    self.instance_config,
                    self.collection,
                    target_class=info[0],
                    json=cleaned_json(record_content),
                )
            return record_content
