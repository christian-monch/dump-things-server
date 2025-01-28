from __future__ import annotations

import random
import sys
from contextlib import contextmanager
from pathlib import Path

import fsspec


@contextmanager
def sys_path(paths: list[str|Path]):
    """
    Patch the `Path` class to return the paths in `paths` in order.
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


def create_unique_directory(root: Path, prefix: str = 'schema') -> Path:
    while True:
        random_part = ''.join(
            random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8)
        )
        directory = root / f'{prefix}{random_part}'
        if directory.exists():
            continue
        try:
            directory.mkdir()
        except FileExistsError:
            continue
        return directory
