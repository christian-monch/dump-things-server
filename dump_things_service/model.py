
import importlib
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import fsspec


def build_model(
    source_url: str,
) -> Any:
    open_file = fsspec.open(source_url, 'rt')
    with open_file as f:
        with tempfile.TemporaryDirectory() as temp_dir:
            definition_file = Path(temp_dir) / 'definition.yaml'
            definition_file.write_text(f.read())
            subprocess.run(
                args=['gen-pydantic', str(definition_file)],
                stdout=(Path(temp_dir) / 'modelx.py').open('w'),
                check=True
            )
            sys.path.insert(0, temp_dir)
            model = importlib.import_module('modelx')
            sys.path.pop(0)
    return model


def get_classes(
    model: Any,
) -> list:
    result = []

    thing_class = type(model.Thing)
    return [name for name, obj in model.__dict__.items() if isinstance(obj, thing_class)]

    for name, definition in model.__dict__.items():
        if isinstance(definition, thing_class):
            print(name, definition)
            result.append(name)
    return result
