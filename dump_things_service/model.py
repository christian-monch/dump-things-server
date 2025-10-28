from __future__ import annotations

import dataclasses  # noqa F401 -- used by generated code
import logging
import sys
from itertools import count
from types import ModuleType
from typing import (
    TYPE_CHECKING,
    Any,
)
from urllib.parse import urlparse

import annotated_types  # noqa F401 -- used by generated code
import pydantic  # noqa F401 -- used by generated code
import pydantic_core  # noqa F401 -- used by generated code
from linkml.generators import (
    PydanticGenerator,
    PythonGenerator,
)
from linkml_runtime import SchemaView
from pydantic._internal._model_construction import ModelMetaclass

# Ensure linkml is patched
import dump_things_service.patches.enabled  # noqa F401 -- apply patches

if TYPE_CHECKING:
    from types import ModuleType

if (sys.version_info.major, sys.version_info.minor) == (3, 11):
    sys.setrecursionlimit(2000)

lgr = logging.getLogger('dump_things_service')

serial_number = count()
_model_counter = count()

_model_cache = {}
_schema_model_cache = {}
_schema_view_cache = {}


# Pydantic module generation might require a higher recursion limit than the
# default. Add a mechanism to increase it as needed, up to a maximum.
max_recursion_limit = 10000
current_recursion_limit = sys.getrecursionlimit()


def get_classes(
    model: Any,
) -> list[str]:
    """get names of all subclasses of Thing"""
    return get_subclasses(model, 'Thing')


def get_subclasses(
    model: ModuleType,
    class_name: str,
) -> list[str]:
    """get names of all subclasses (includes class_name itself)"""
    super_class = getattr(model, class_name)
    return [
        name
        for name, obj in model.__dict__.items()
        if isinstance(obj, ModelMetaclass) and issubclass(obj, super_class)
    ]


def compile_module_with_increasing_recursion_limit(
    pydantic_generator: PydanticGenerator,
    schema_location: str,
) -> ModuleType:
    global current_recursion_limit

    module = None
    module_name = (
        urlparse(schema_location).path
        .replace('/', '_')
        .replace('-', '_')
        .replace('.', '_')
    )
    while module is None:
        try:
            module = pydantic_generator.compile_module(module_name=module_name)
        except RecursionError:
            if current_recursion_limit >= max_recursion_limit:
                lgr.error(
                    f'Maximum recursion limit ({max_recursion_limit}) reached when '
                    'building Pydantic model, cannot increase further.'
                )
                raise
            current_recursion_limit += 1000
            sys.setrecursionlimit(current_recursion_limit)
            lgr.warning(
                'RecursionError when building Pydantic model for schema '
                f'{schema_location}, increasing recursion limit to: '
                f'{current_recursion_limit}.'
            )
    return module


def get_model_for_schema(
    schema_location: str,
) -> tuple[ModuleType, list[str], str]:
    if schema_location not in _model_cache:
        lgr.info(f'Building model for schema {schema_location}.')
        pydantic_generator = PydanticGenerator(schema_location)
        model = compile_module_with_increasing_recursion_limit(
            pydantic_generator,
            schema_location,
        )
        classes = get_classes(model)
        model_var_name = f'model_{next(_model_counter)}'
        _model_cache[schema_location] = model, classes, model_var_name
    return _model_cache[schema_location]


def get_schema_view(schema_location: str) -> SchemaView:
    if schema_location not in _schema_view_cache:
        _schema_view_cache[schema_location] = SchemaView(schema_location)
    return _schema_view_cache[schema_location]


def get_schema_model_for_schema(
    schema_location: str,
) -> ModuleType:
    if schema_location not in _schema_model_cache:
        _schema_model_cache[schema_location] = PythonGenerator(
            schema_location
        ).compile_module()
    return _schema_model_cache[schema_location]
