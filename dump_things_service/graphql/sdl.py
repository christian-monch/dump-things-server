from __future__ import annotations

import importlib
import subprocess
import sys
import tempfile
from itertools import count
from pathlib import Path
from typing import Any

from dump_things_service.utils import (
    read_url,
    sys_path,
)


__all__ = [
    'generate_graphql_module_from_linkml',
]


serial_number = count()


created_modules: dict[tuple[str, tuple[str, ...]], Any] = {}


def _generate_graphql_from_linkml(
    temp_dir: Path,
    linkml_schema_url: str,
    scalars: list[str] | None = None,
) -> Path:
    """
    Generate a GraphQL schema from a LinkML schema.

    This method uses LinkML's `gen-graphql` command to generate a GraphQL
    schema from a LinkML-schema. It adds the provided scalars tp the schema.

    :param temp_dir: Directory in which linkml and graphql files are generated,
        existing files might be overwritten.
    :param linkml_schema_url: URL of the LinkML schema.
    :param scalars: List of scalar types to include in the GraphQL schema.
    :return: A string representing the GraphQL schema with the specified
        scalars included.
    """
    linkml_schema_path = Path(temp_dir) / f'linkml-schema.yaml'
    linkml_schema_path.write_text(read_url(linkml_schema_url))

    graphql_schema_path = Path(temp_dir) / f'graphql-schema.graphql'
    with graphql_schema_path.open('w') as graphql_schema_file:
        graphql_schema_file.write(
            '\n'.join([f'scalar {scalar}' for scalar in scalars or []])
        )
        graphql_schema_file.flush()

        subprocess.run(
            args=['gen-graphql', str(linkml_schema_path)],
            stdout=graphql_schema_file,
            check=True,
        )

    return graphql_schema_path


def _generate_module_from_graphql(
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
    scalars: list[str] | None = None,
) -> Any:
    """
    Generate a GraphQL schema from a LinkML schema URL.

    :param linkml_schema_url: URL of the LinkML schema.
    :param scalars: List of scalar types to include in the GraphQL schema.
    :return: A Python module representing the generated GraphQL schema.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        graphql_schema_path = _generate_graphql_from_linkml(
            temp_dir_path,
            linkml_schema_url,
            scalars,
        )

        return _generate_module_from_graphql(
            temp_dir_path,
            graphql_schema_path,
        )


def get_graphql_module_for_linkml_schema(
    linkml_schema_url: str,
    scalars: list[str] | None = None,
) -> Any:
    scalar_key = tuple(sorted(scalars or []))
    if (linkml_schema_url, scalar_key) not in created_modules:
        created_modules[(linkml_schema_url, scalar_key)] = (
            generate_graphql_module_from_linkml(linkml_schema_url, scalars)
        )
    return created_modules[(linkml_schema_url, scalar_key)]
