from __future__ import annotations

import dataclasses  # noqa F401 -- used by generated code
import importlib
import logging
import subprocess
import tempfile
from itertools import count
from pathlib import Path
from typing import Any

import annotated_types  # noqa F401 -- used by generated code
import pydantic  # noqa F401 -- used by generated code
import pydantic_core  # noqa F401 -- used by generated code
from pydantic._internal._model_construction import ModelMetaclass

from dump_things_service.utils import (
    read_url,
    sys_path,
)

lgr = logging.getLogger('uvicorn')

serial_number = count()
_model_counter = count()
_model_cache = {}


def build_model(
    source_url: str,
) -> Any:
    with tempfile.TemporaryDirectory() as temp_dir:
        module_name = f'model_{next(serial_number)}'
        definition_file = Path(temp_dir) / 'definition.yaml'
        definition_file.write_text(read_url(source_url))
        subprocess.run(
            args=['gen-pydantic', str(definition_file)],
            stdout=(Path(temp_dir) / (module_name + '.py')).open('w'),
            check=True,
        )
        with sys_path([temp_dir]):
            model = importlib.import_module(module_name)
    return model


def get_classes(
    model: Any,
) -> list:
    """get names of all subclasses of Thing"""
    return get_subclasses(model, 'Thing')


def get_subclasses(
    model: Any,
    class_name: str,
) -> list:
    """get names of all subclasses (includes class_name itself)"""
    super_class = getattr(model, class_name)
    return [
        name
        for name, obj in model.__dict__.items()
        if isinstance(obj, ModelMetaclass) and issubclass(obj, super_class)
    ]


def get_model_for_schema(
    schema_location: str,
) -> tuple[Any, list[str], str]:
    if schema_location not in _model_cache:
        lgr.info(f'Building model for schema {schema_location}.')
        model = build_model(schema_location)
        classes = get_classes(model)
        model_var_name = f'model_{next(_model_counter)}'
        _model_cache[schema_location] = model, classes, model_var_name
    return _model_cache[schema_location]
