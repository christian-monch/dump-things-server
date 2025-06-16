from __future__ import annotations

import importlib
import subprocess
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
from dump_things_service.graphql.graphql_generator import GraphQLGenerator

if TYPE_CHECKING:
    from types import ModuleType


__all__ = [
    'generate_graphql_module_from_linkml',
]


serial_number = count()


created_modules: dict[str, ModuleType] = {}


def _generate_graphql_from_linkml(
    temp_dir: Path,
    linkml_schema_url: str,
) -> Path:
    """
    Generate a GraphQL schema from a LinkML schema.

    :param temp_dir: Directory in which linkml and graphql files are generated,
        existing files might be overwritten.
    :param linkml_schema_url: URL of the LinkML schema.
    :return: A path where the resulting GraphQL schema is stored.
    """
    # Fetch linkml schema from URL and store it in a temporary file
    linkml_schema_path = Path(temp_dir) / f'linkml-schema.yaml'
    linkml_schema_path.write_text(read_url(linkml_schema_url))

    # Generate GraphQL schema from LinkML schema
    graphql_schema_generator = GraphQLGenerator(str(linkml_schema_path))
    graphql_schema = graphql_schema_generator.serialize()

    # Store the GraphQL schema in a temporary file
    graphql_schema_path = Path(temp_dir) / f'graphql-schema.graphql'
    graphql_schema_path.write_text(graphql_schema)
    return graphql_schema_path


def _generate_strawberry_module_from_graphql(
    temp_dir: Path,
    graphql_schema_path: Path,
) -> Any:
    """
    Generate a Python module from a GraphQL schema string.

    This method uses the `gen-pydantic` command to generate a Python module
    from the provided GraphQL schema string.

    :param temp_dir: Directory in which the Python module is generated.
    :param graphql_schema_path: Path to the stored GraphQL schema.
    :return: The generated Python module.
    """
    module_name = f'graphql_module_{next(serial_number)}'
    with (temp_dir / (module_name + '.py')).open('w') as module_file:
        module_file.write('from __future__ import annotations\n\n')
        module_file.flush()
        subprocess.run(
            args=['strawberry', 'schema-codegen', str(graphql_schema_path)],
            stdout=module_file,
            check=True,
        )
    with sys_path([temp_dir] + sys.path):
        return importlib.import_module(module_name)


def generate_graphql_module_from_linkml(
    linkml_schema_url: str,
) -> ModuleType:
    """
    Generate a GraphQL schema from a LinkML schema URL.

    :param linkml_schema_url: URL of the LinkML schema.
    :return: A Python module representing the generated GraphQL schema.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        graphql_schema_path = _generate_graphql_from_linkml(
            temp_dir_path,
            linkml_schema_url,
        )

        return _generate_strawberry_module_from_graphql(
            temp_dir_path,
            graphql_schema_path,
        )


def get_strawberry_module_for_linkml_schema(linkml_schema_url: str) -> Any:
    if linkml_schema_url not in created_modules:
        created_modules[linkml_schema_url] = (
            generate_graphql_module_from_linkml(linkml_schema_url)
        )
    return created_modules[linkml_schema_url]


if __name__ == "__main__":
    print(get_strawberry_module_for_linkml_schema(sys.argv[1]))
