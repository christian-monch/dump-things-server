from __future__ import annotations

import types
from itertools import count
from typing import Any, TYPE_CHECKING

from linkml.generators import PydanticGenerator
from pydantic._internal._model_construction import ModelMetaclass

if TYPE_CHECKING:
    import types

serial_number = count()


def build_model(
    source_url: str,
) -> types.ModuleType:
    return PydanticGenerator(source_url).compile_module()


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
