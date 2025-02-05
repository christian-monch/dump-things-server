from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path

import fsspec

from . import JSON


@contextmanager
def sys_path(paths: list[str|Path]):
    """Patch the `Path` class to return the paths in `paths` in order.
    """
    original_path = sys.path
    try:
        sys.path = [str(path) for path in paths]
        yield
    finally:
        sys.path = original_path


def read_url(url: str) -> str:
    """
    Read the content of an URL into memory.
    """
    open_file = fsspec.open(url, 'rt')
    with open_file as f:
        return f.read()


def cleaned_json(
        data: JSON,
        remove_keys: tuple[str] = ('@type', 'schema_type')
) -> JSON:
    if isinstance(data, list):
        return [cleaned_json(item, remove_keys) for item in data]
    elif isinstance(data, dict):
        return {
            key: cleaned_json(value, remove_keys)
            for key, value in data.items()
            if key not in remove_keys
        }
    else:
        return data
