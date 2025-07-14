from __future__ import annotations

import sys
from argparse import ArgumentParser
from pathlib import Path

from dump_things_service.backends import StorageBackend
from dump_things_service.backends.record_dir import RecordDirStore
from dump_things_service.backends.sqlite import SQLiteBackend


parser = ArgumentParser(
    prog='Copy collection  content from source store to destination store',
    description='Copy the records of a collection that is stored in the '
                'source-store to the destination-store. This command copies '
                'records without validation of their content.',
)
parser.add_argument(
    'source',
    help='The source store. The format is: `<backend>:<directory-path>. '
         'Supported backends are: "sqlite", and "record_dir". If the source '
         'store is a record_dir`-store its index is used to locate the source '
         'records.',
)
parser.add_argument(
    'destination',
    help='The destination store. The format is: `<backend>:<directory-path>. '
         'Supported backends are: "sqlite", and "record_dir".',
)
parser.add_argument(
    '-c', '--config',
    metavar='CONFIG_FILE',
    help='Read the configuration from \'CONFIG_FILE\' instead of looking for '
         'it in the directory of the `record_dir`-store.'
)


def get_backend(backend_spec: str) -> StorageBackend:
    if ':' not in backend_spec:
        msg = (
            f'Invalid backend specification: {backend_spec}. The format is '
            '"<backend>:<path>", where "<backend>" is one of: `record_dir`, '
            '`sqlite`.'
        )
        raise ValueError(msg)

    backend_type, location = backend_spec.split(':', 1)
    if backend_type == 'record_dir':
        return RecordDirStore(
            root=Path(location),
            pid_mapping_function=lambda x: x,
            suffix='',
        )
    elif backend_type == 'sqlite':
        return SQLiteBackend(
            db_path=Path(location) / '.records.db',
        )
    else:
        msg = (
            f'Invalid backend type: {backend_type}. Backend type should be one '
            f'of: `record_dir`, `sqlite`.'
        )
        raise ValueError(msg)


def copy_records(
    source: StorageBackend,
    destination: StorageBackend,
):
    source_records = source.get_records_of_classes(['Thing'])
    destination.add_records_bulk(source_records)


def main():
    arguments = parser.parse_args()

    source = get_backend(arguments.source)
    destination = get_backend(arguments.destination)
    copy_records(source, destination)
    return 0


if __name__ == "__main__":
    sys.exit(main())
