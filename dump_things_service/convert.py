from __future__ import annotations

import re
from datetime import datetime
from json import (
    loads as json_loads,
)
from typing import TYPE_CHECKING

from fastapi import HTTPException
from linkml.generators import PythonGenerator
from linkml.utils.datautils import (
    get_dumper,
    get_loader,
)
from linkml_runtime import SchemaView
from rdflib.term import (
    URIRef,
    bind,
)

from dump_things_service import (
    HTTP_400_BAD_REQUEST,
    JSON,
    Format,
)
from dump_things_service.utils import cleaned_json

if TYPE_CHECKING:
    import types

    from pydantic import BaseModel

    from dump_things_service.config import InstanceConfig


datetime_regex = re.compile(r'^([-+]\d+)|(\d{4})|(\d{4}-[01]\d)|(\d{4}-[01]\d-[0-3]\d)|(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d\.\d+([+-][0-2]\d:[0-5]\d|Z))|(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d([+-][0-2]\d:[0-5]\d|Z))|(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d([+-][0-2]\d:[0-5]\d|Z))$')

def validate_datetime(value: str) -> str:
    match = datetime_regex.match(value)
    if not match:
        msg = 'Invalid datetime format: {value}'
        raise ValueError(msg)
    return value


# Enable rdflib to parse date time literals
bind(
    datatype=URIRef('https://www.w3.org/TR/NOTE-datetime'),
    constructor=validate_datetime,
    pythontype=datetime,
)


def convert_json_to_ttl(
    instance_config: InstanceConfig,
    collection_name: str,
    target_class: str,
    json: JSON,
) -> str:

    # Because we do not store type information in the records that we store,
    # we use pydantic's ability to infer the type from the data.
    pydantic_object = getattr(
        instance_config.model_info[collection_name][0],
        target_class
    )(**json)

    return convert_pydantic_to_ttl(
        instance_config=instance_config,
        collection_name=collection_name,
        pydantic_object=pydantic_object,
    )


def convert_pydantic_to_ttl(
    instance_config: InstanceConfig,
    collection_name: str,
    pydantic_object: BaseModel,
):
    from dump_things_service.config import get_conversion_objects_for_collection

    return convert_format(
        target_class=pydantic_object.__class__.__name__,
        data=pydantic_object.model_dump(mode='json', exclude_none=True),
        input_format=Format.json,
        output_format=Format.ttl,
        **get_conversion_objects_for_collection(instance_config, collection_name),
    )


def convert_ttl_to_json(
    instance_config: InstanceConfig,
    collection_name: str,
    target_class: str,
    ttl: str,
) -> JSON:
    from dump_things_service.config import get_conversion_objects_for_collection

    json_string = convert_format(
        target_class=target_class,
        data=ttl,
        input_format=Format.ttl,
        output_format=Format.json,
        **get_conversion_objects_for_collection(instance_config, collection_name),
    )
    return cleaned_json(json_loads(json_string))


def convert_format(
    target_class: str,
    data: JSON | str,
    input_format: Format,
    output_format: Format,
    schema_module: types.ModuleType,
    schema_view: SchemaView,
) -> str:
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
            schema_module=schema_module,
            schema_view=schema_view,
        )
    except Exception as e:  # BLE001
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail='Conversion error: ' + str(e)
        ) from e


def _convert_format(
    target_class: str,
    data: JSON | str,
    input_format: Format,
    output_format: Format,
    schema_module: types.ModuleType,
    schema_view: SchemaView,
) -> str:
    """Convert between different representations of schema:target_class instances

    The schema information is provided by `schema_module` and `schema_view`.
    Both can be created with `get_convertion_objects`
    """

    if input_format == output_format:
        return data

    py_target_class = schema_module.__dict__[target_class]
    loader = get_loader(input_format.value)
    if input_format.value in ('ttl',):
        input_args = {'schemaview': schema_view, 'fmt': input_format.value}
    else:
        input_args = {}

    data_obj = loader.load(
        source=data,
        target_class=py_target_class,
        **input_args,
    )

    dumper = get_dumper(output_format.value)
    return dumper.dumps(
        data_obj, **({'schemaview': schema_view} if output_format == Format.ttl else {})
    )


def get_conversion_objects(schema: str):
    return {
        'schema_module': PythonGenerator(schema).compile_module(),
        'schema_view': SchemaView(schema),
    }
