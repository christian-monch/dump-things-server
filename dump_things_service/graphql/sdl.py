from __future__ import annotations

import importlib
import sys
import tempfile
from itertools import count
from pathlib import Path
from typing import Any
from typing import TYPE_CHECKING

from dump_things_service.utils import (
    read_url,
    sys_path,
)
from dump_things_service.graphql.strawberry_generator import get_strawberry_source

if TYPE_CHECKING:
    from types import ModuleType


__all__ = [
    'get_strawberry_module_for_linkml_schema',
]


module_name = 'dump_thing_service_graphql_strawberry_module'

created_modules: dict[str, ModuleType] = {}


def generate_strawberry_module_from_linkml(
    linkml_schema_url: str,
) -> ModuleType:
    """
    Generate a strawberry module from a LinkML schema URL.

    :param linkml_schema_url: URL of the LinkML schema.
    :return: A Python module representing the generated GraphQL schema.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        # Fetch linkml schema from URL and store it in a temporary file
        linkml_schema_path = temp_dir_path / f'linkml-schema.yaml'
        linkml_schema_path.write_text(read_url(linkml_schema_url))

        # Generate strawberry module schema from LinkML schema
        module_source = get_strawberry_source(linkml_schema_path)
        module_file = temp_dir_path / (module_name + '.py')
        module_file.write_text(module_source)

        with sys_path([temp_dir] + sys.path):
            return importlib.import_module(module_name)


def get_strawberry_module_for_linkml_schema(linkml_schema_url: str) -> Any:
    if linkml_schema_url not in created_modules:
        created_modules[linkml_schema_url] = (
            generate_strawberry_module_from_linkml(linkml_schema_url)
        )
    return created_modules[linkml_schema_url]


if __name__ == "__main__":
    print(get_strawberry_module_for_linkml_schema(sys.argv[1]))
