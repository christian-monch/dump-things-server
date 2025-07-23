from __future__ import annotations

import re
from json import loads as json_loads
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
)

from linkml.utils.datautils import (
    get_dumper,
    get_loader,
)
from linkml_runtime import SchemaView
from rdflib.term import (
    URIRef,
    bind,
)

from dump_things_service import Format
from dump_things_service.lazy_list import LazyList
from dump_things_service.model import (
    get_model_for_schema,
    get_schema_model_for_schema,
)
from dump_things_service.utils import cleaned_json

if TYPE_CHECKING:
    from types import ModuleType

    from pydantic import BaseModel

    from dump_things_service.backends import RecordInfo


_cached_conversion_objects = {}


# Enable rdflib to parse date time literals with type ref:
# `https://www.w3.org/TR/NOTE-datetime`. We add a regex-based validation and
# return the validated datetime string verbatim.

_datetime_regex = re.compile(
    r'^([-+]\d+)|(\d{4})|(\d{4}-[01]\d)|(\d{4}-[01]\d-[0-3]\d)|(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d\.\d+([+-][0-2]\d:[0-5]\d|Z))|(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d([+-][0-2]\d:[0-5]\d|Z))|(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d([+-][0-2]\d:[0-5]\d|Z))$'
)


def _validate_datetime(value: str) -> str:
    match = _datetime_regex.match(value)
    if not match:
        msg = 'Invalid datetime format: {value}'
        raise ValueError(msg)
    return value


bind(
    datatype=URIRef('https://www.w3.org/TR/NOTE-datetime'),
    constructor=_validate_datetime,
    pythontype=str,
)


def get_conversion_objects(schema: str):
    if schema not in _cached_conversion_objects:
        _cached_conversion_objects[schema] = {
            'schema_module': get_schema_model_for_schema(schema),
            'schema_view': SchemaView(schema),
        }
    return _cached_conversion_objects[schema]


class FormatConverter:
    def __init__(
        self,
        schema: str,
        input_format: Format,
        output_format: Format,
    ):
        self.converter = self._check_formats(input_format, output_format)
        self.model = get_model_for_schema(schema)[0]
        self.conversion_objects = get_conversion_objects(schema)

    def _check_formats(
        self,
        input_format: Format,
        output_format: Format,
    ) -> Callable:
        if input_format == output_format:
            return lambda data, _: data
        if input_format == Format.ttl:
            return self._convert_ttl_to_json
        return self._convert_json_to_ttl

    def convert(self, data: str | dict, target_class: str) -> str | dict:
        return self.converter(data, target_class)

    def _convert_json_to_ttl(
        self,
        data: dict,
        target_class: str,
    ) -> str:
        pydantic_object = getattr(self.model, target_class)(**data)
        return self._convert_pydantic_to_ttl(pydantic_object=pydantic_object)

    def _convert_pydantic_to_ttl(
        self,
        pydantic_object: BaseModel,
    ):
        return _convert_format(
            target_class=pydantic_object.__class__.__name__,
            data=pydantic_object.model_dump(mode='json', exclude_none=True),
            input_format=Format.json,
            output_format=Format.ttl,
            **self.conversion_objects,
        )

    def _convert_ttl_to_json(
        self,
        data: str,
        target_class: str,
    ) -> dict:
        json_string = _convert_format(
            target_class=target_class,
            data=data,
            input_format=Format.ttl,
            output_format=Format.json,
            **self.conversion_objects,
        )
        return cleaned_json(json_loads(json_string))


class ConvertingList(LazyList):
    """
    A lazy list that converts records stored in an "input" lazy list. The
    input lazy list must return `RecordInfo`-objects.
    """

    def __init__(
        self,
        input_list: LazyList,
        schema: str,
        input_format: Format,
        output_format: Format,
        exception_handler: Callable | None = None,
    ):
        super().__init__()
        self.input_list = input_list
        # We reuse `list_info` from the input list to save time and memory.
        self.list_info = input_list.list_info
        self.exception_handler: Callable | None = exception_handler
        self.converter = FormatConverter(schema, input_format, output_format)

    def generate_element(self, index: int, _: Any) -> Any:
        record_info: RecordInfo = self.input_list[index]
        try:
            record_info.json_object = self.converter.convert(
                data=record_info.json_object,
                target_class=record_info.class_name,
            )
        except BaseException as e:
            if self.exception_handler:
                self.exception_handler(e)
            else:
                raise
        return record_info.json_object


def _convert_format(
    target_class: str,
    data: dict | str,
    input_format: Format,
    output_format: Format,
    schema_module: ModuleType,
    schema_view: SchemaView,
) -> str:
    """Convert between different representations of schema:target_class instances

    The schema information is provided by `schema_module` and `schema_view`.
    Both can be created with `get_convertion_objects`
    """
    try:
        return _do_convert_format(
            target_class=target_class,
            data=data,
            input_format=input_format,
            output_format=output_format,
            schema_module=schema_module,
            schema_view=schema_view,
        )
    except Exception as e:  # BLE001
        msg = (
            f'Conversion {input_format} -> {output_format}. Error: {e}, '
            f'target class {target_class}, data:\n{data}'
        )
        raise ValueError(msg) from e


def _do_convert_format(
    target_class: str,
    data: dict | str,
    input_format: Format,
    output_format: Format,
    schema_module: ModuleType,
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
