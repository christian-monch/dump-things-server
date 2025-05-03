from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException
from linkml.generators import PythonGenerator
from linkml.utils.datautils import (
    get_dumper,
    get_loader,
)
from linkml_runtime import SchemaView

from dump_things_service import (
    JSON,
    Format,
)

if TYPE_CHECKING:
    import types


def convert_json_to_ttl(
    collection_name: str,
    target_class: str,
    json: JSON,
) -> str:
    from main import (
        g_schemas,
        g_conversion_objects,
    )

    return convert_format(
        target_class=target_class,
        data=json,
        input_format=Format.json,
        output_format=Format.ttl,
        **g_conversion_objects[g_schemas[collection_name]],
    )


def convert_ttl_to_json(
        collection_name: str,
        target_class: str,
        ttl: str,
) -> str:
    from main import (
        g_schemas,
        g_conversion_objects,
    )
    return convert_format(
        target_class=target_class,
        data=ttl,
        input_format=Format.ttl,
        output_format=Format.json,
        **g_conversion_objects[g_schemas[collection_name]],
    )


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
            status_code=404, detail='Conversion error: ' + str(e)
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

#def get_conversion_objects(collections: dict[str, tuple[CollectionDirConfig]]):
#    return {
#        collection_name: {
#            'schema_module': PythonGenerator(dir_config.schema).compile_module(),
#            'schema_view': SchemaView(dir_config.schema),
#        }
#        for collection_name, dir_config in collections.items()
#    }
