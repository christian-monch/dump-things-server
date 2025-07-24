from __future__ import annotations

import sys
from contextlib import contextmanager
from functools import reduce
from typing import TYPE_CHECKING

import fsspec
from fastapi import HTTPException
from rdflib import Graph

from dump_things_service import HTTP_400_BAD_REQUEST

if TYPE_CHECKING:
    from pathlib import Path

    from dump_things_service import JSON
    from dump_things_service.config import InstanceConfig


@contextmanager
def sys_path(paths: list[str | Path]):
    """Patch the `Path` class to return the paths in `paths` in order."""
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


def cleaned_json(data: JSON, remove_keys: tuple[str, ...] = ('@type',)) -> JSON:
    if isinstance(data, list):
        return [cleaned_json(item, remove_keys) for item in data]
    if isinstance(data, dict):
        return {
            key: cleaned_json(value, remove_keys)
            for key, value in data.items()
            if key not in remove_keys and data[key] is not None
        }
    return data


def combine_ttl(documents: list[str]) -> str:
    graphs = [Graph().parse(data=doc, format='ttl') for doc in documents]
    return reduce(lambda g1, g2: g1 + g2, graphs).serialize(format='ttl')


def get_schema_type_curie(
    instance_config: InstanceConfig,
    collection: str,
    class_name: str,
) -> str:
    schema_url = instance_config.schemas[collection]
    schema_module = instance_config.conversion_objects[schema_url]['schema_module']
    class_object = getattr(schema_module, class_name)
    return class_object.class_class_curie


@contextmanager
def wrap_http_exception(
    exception_class: type[BaseException] = ValueError,
    status_code: int = HTTP_400_BAD_REQUEST,
    header: str = ''
):
    """Wrap exceptions of class `exception_class` into HTTP exceptions"""
    try:
        yield
    except exception_class as e:
        raise HTTPException(
            status_code=status_code,
            detail=f'{header}: {e}' if header else str(e),
        )
