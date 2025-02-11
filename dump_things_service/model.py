from __future__ import annotations

import importlib
import subprocess
import tempfile
from itertools import count
from pathlib import Path
from typing import Any

from .utils import (
    read_url,
    sys_path,
)


serial_number = count()


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
            check=True
        )
        with sys_path([temp_dir]):
            model = importlib.import_module(module_name)
    return model


def get_classes(
    model: Any,
) -> list:

    def is_thing_subclass(obj):
        while obj is not None:
            if obj is model.Thing:
                return True
            obj = getattr(obj, '__base__', None)

    return [
        name
        for name, obj in model.__dict__.items()
        if is_thing_subclass(obj)
    ]
