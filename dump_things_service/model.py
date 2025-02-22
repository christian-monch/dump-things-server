from __future__ import annotations

import dataclasses  # noqa F401 -- used by generated code
import importlib
import subprocess
import tempfile
import types
from itertools import count
from pathlib import Path
from typing import Any, TYPE_CHECKING

import annotated_types  # noqa F401 -- used by generated code
import pydantic  # noqa F401 -- used by generated code
import pydantic_core  # noqa F401 -- used by generated code
from pydantic._internal._model_construction import ModelMetaclass

from dump_things_service.utils import (
    read_url,
    sys_path,
)

if TYPE_CHECKING:
    import types

serial_number = count()


def build_model(
    source_url: str,
) -> types.ModuleType:
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
    def is_thing_subclass(obj) -> bool:
        while obj is not None:
            if obj is model.Thing:
                return True
            obj = getattr(obj, '__base__', None)
        return False

    return [name for name, obj in model.__dict__.items() if is_thing_subclass(obj)]


def get_subclasses(
    model: Any,
    class_name: str,
) -> list:
    """get names of all subclasses (includes class_name itself)"""

    def is_subclass(obj) -> bool:
        while obj is not None and isinstance(obj, ModelMetaclass):
            if obj.__name__ == class_name:
                return True
            obj = getattr(obj, '__base__', None)
        return False

    return [name for name, obj in model.__dict__.items() if is_subclass(obj)]
