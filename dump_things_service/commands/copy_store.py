from __future__ import annotations

import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import TYPE_CHECKING

from dump_things_service.backends.record_dir import (
    RecordDirStore,
    _RecordDirStore,
)
from dump_things_service.backends.schema_type_layer import SchemaTypeLayer
from dump_things_service.backends.sqlite import (
    SQLiteBackend,
    _SQLiteBackend,
)
from dump_things_service.backends.sqlite import (
    record_file_name as sqlite_record_file_name,
)
from dump_things_service.config import get_backend_and_extension

if TYPE_CHECKING:
    from dump_things_service.backends import StorageBackend


parser = ArgumentParser(
    prog='Copy collection content from source store to destination store',
    description='Copy the records of a collection that is stored in the '
    'source-store to the destination-store. This command copies '
    'records without validation of their content.',
)
parser.add_argument(
    'source',
    help='The source store. The format is: `<backend>:<directory-path>. '
    'Supported backends are: "record_dir", "record_dir_stl", and '
    '"sqlite". If the source store is a "record_dir"-store or a '
    '"record_dir_stl"-store, its index is used to locate the source '
    'records.',
)
parser.add_argument(
    'destination',
    help='The destination store. The format is: `<backend>:<directory-path>. '
    'Supported backends are: "record_dir", "record_dir_stl", and "sqlite".',
)
parser.add_argument(
    '-c',
    '--config',
    metavar='CONFIG_FILE',
    help="Read the configuration from 'CONFIG_FILE' instead of looking for "
    'it in the directory of the `record_dir`-store.',
)
parser.add_argument(
    '-s',
    '--schema',
    metavar='SCHEMA',
    help='If any of the stores uses a `record_dir_stl`-backend, use the given '
    '`SCHEMA` to determine the correct class-URI for added '
    '`schema_type`-attributes.',
)


def get_backend(
    backend_spec: str,
    schema: str | None = None,
) -> StorageBackend:
    if ':' not in backend_spec:
        msg = (
            f'Invalid backend specification: {backend_spec}. The format is '
            '"<backend>:<path>", where "<backend>" is one of: `record_dir`, '
            '`sqlite`.'
        )
        raise ValueError(msg)

    backend_type, location = backend_spec.split(':', 1)
    location = Path(location).absolute()
    if not location.is_dir():
        msg = f'location must be a directory: {location}'
        raise ValueError(msg)

    backend_name, extension = get_backend_and_extension(backend_type)
    if backend_name == 'record_dir':
        backend = RecordDirStore(
            root=location,
            pid_mapping_function=lambda x: x,
            suffix='',
        )
    elif backend_name == 'sqlite':
        backend = SQLiteBackend(
            db_path=location / sqlite_record_file_name,
        )
    else:
        msg = (
            f'Invalid backend type: {backend_type}. Supported backend types '
            f'are: `record_dir`, `record_dir+stl`, `sqlite`, and `sqlite+stl`.'
        )
        raise ValueError(msg)

    if extension == 'stl':
        if schema is None:
            msg = (
                f'A `{backend_name}+stl`-backend requires a schema. Use '
                '`-s/--schema` to provide one.'
            )
            raise ValueError(msg)
        backend = SchemaTypeLayer(
            backend=backend,
            schema=schema,
        )
    return backend


def copy_records(
    source: StorageBackend,
    destination: StorageBackend,
):
    destination.add_records_bulk(source.get_all_records())


def needs_copy(
    source: StorageBackend,
    destination: StorageBackend,
) -> bool:
    if isinstance(source, _RecordDirStore) and isinstance(destination, _RecordDirStore):
        return source.root != destination.root
    if isinstance(source, _SQLiteBackend) and isinstance(destination, _SQLiteBackend):
        return source.db_path != destination.db_path
    return True


def main():
    arguments = parser.parse_args()

    source = get_backend(
        backend_spec=arguments.source,
        schema=arguments.schema,
    )
    destination = get_backend(
        backend_spec=arguments.destination,
        schema=arguments.schema,
    )

    if needs_copy(source, destination):
        copy_records(source, destination)

    return 0


if __name__ == '__main__':
    sys.exit(main())
