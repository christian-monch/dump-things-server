from __future__ import annotations

from json import (
    dumps as json_dumps,
)
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

from dump_things_service import (
    HTTP_400_BAD_REQUEST,
    JSON,
    Format,
)
from dump_things_service.utils import cleaned_json

if TYPE_CHECKING:
    import types


def convert_json_to_ttl(
    collection_name: str,
    target_class: str,
    json: JSON,
) -> str:
    from dump_things_service.main import (
        g_conversion_objects,
        g_schemas,
    )

    return convert_format(
        target_class=target_class,
        data=json_dumps(json),
        input_format=Format.json,
        output_format=Format.ttl,
        **g_conversion_objects[g_schemas[collection_name]],
    )


def convert_ttl_to_json(
    collection_name: str,
    target_class: str,
    ttl: str,
) -> JSON:
    from dump_things_service.main import (
        g_conversion_objects,
        g_schemas,
    )

    json_string = convert_format(
        target_class=target_class,
        data=ttl,
        input_format=Format.ttl,
        output_format=Format.json,
        **g_conversion_objects[g_schemas[collection_name]],
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
