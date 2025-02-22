from __future__ import annotations

import json
from typing import TYPE_CHECKING

from fastapi import HTTPException
from linkml.utils.datautils import (
    get_dumper,
    get_loader,
)
from pydantic import BaseModel

from dump_things_service import Format
from dump_things_service.utils import cleaned_json

if TYPE_CHECKING:
    from dump_things_service.backends.interface import CollectionInfo


def convert_format(
    target_class: str,
    data: BaseModel | str,
    input_format: Format,
    output_format: Format,
    collection_info: CollectionInfo,
) -> BaseModel | str:
    """Convert between different representations of schema:target_class instances

    The schema information is provided by `schema_module` and `schema_view`.
    Both can be created with `get_convertion_objects`
    """
    try:
        return _convert_format(
            target_class=target_class,
            data=data,
            input_format=input_format,
            output_format=output_format,
            collection_info=collection_info,
        )
    except Exception as e:  # BLE001
        raise HTTPException(
            status_code=404, detail='Conversion error: ' + str(e)
        ) from e


def _convert_format(
    target_class: str,
    data: BaseModel | str,
    input_format: Format,
    output_format: Format,
    collection_info: CollectionInfo,
) -> BaseModel | str:
    """Convert between different representations of schema:target_class instances

    The schema information is provided by `schema_module` and `schema_view`.
    Both can be created with `get_convertion_objects`
    """

    if input_format == output_format:
        return data

    schema_module, schema_view = collection_info.schema_module, collection_info.schema_view

    py_target_class = schema_module.__dict__[target_class]
    loader = get_loader(input_format.value)
    if input_format.value in ('ttl',):
        input_args = {'schemaview': schema_view, 'fmt': input_format.value}
    else:
        input_args = {}
        data = cleaned_json(data.model_dump(exclude_none=True))

    data_obj = loader.load(
        source=data,
        target_class=py_target_class,
        **input_args,
    )

    dumper = get_dumper(output_format.value)
    result = dumper.dumps(
        data_obj, **({'schemaview': schema_view} if output_format == Format.ttl else {})
    )
    if output_format == Format.json:
        return collection_info.model.__dict__[target_class](
            **cleaned_json(json.loads(result))
        )
    return result
