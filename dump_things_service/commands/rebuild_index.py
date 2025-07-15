from __future__ import annotations

import sys
from argparse import ArgumentParser
from pathlib import Path

import yaml

from dump_things_service import config_file_name
from dump_things_service.backends.record_dir_index import RecordDirIndex
from dump_things_service.config import CollectionDirConfig

parser = ArgumentParser(
    prog='Rebuild the index of a `record_dir`-store',
    description='This command rebuilds the index of a `record_dir`-store. '
    'This is necessary if the content of a `record_dir`-store was '
    'modified externally, e.g., by adding or deleting files in '
    'the `record_dir`-directory.',
)
parser.add_argument(
    'store',
    help='The directory of the `record_dir`-store, for which the index should '
    'be rebuild.',
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
    metavar='SCHEMA_URL',
    help='The schema that should be used for pid-expansion. This overrides '
    'the schema defined in a configuration file.',
)
parser.add_argument(
    '-f',
    '--format',
    metavar='FORMAT',
    default='yaml',
    help='The format (and suffix) of records in the `record_dir`-store. This '
    'overrides the format defined in a configuration file.',
)


def process_config(arguments) -> tuple[Path, str, str]:
    store = Path(arguments.store)

    suffix = arguments.format if arguments.format else None
    schema = arguments.schema if arguments.schema else None
    if suffix is not None and schema is not None:
        return store, schema, suffix

    # At least on if `suffix` and `schema` has to come from a configuration
    # file.
    config_path = (
        Path(arguments.config) if arguments.config else store / config_file_name
    )
    config_object = CollectionDirConfig(
        **yaml.load(config_path.read_text(), Loader=yaml.SafeLoader)
    )
    return (
        store,
        schema if schema else config_object.schema,
        suffix if suffix else config_object.format,
    )


def rebuild_index(
    store: Path, schema: str, suffix: str, order_by: list[str] | None = None
):
    index = RecordDirIndex(
        store_dir=store.absolute(),
        suffix=suffix,
    )
    index.rebuild_index(schema=schema, order_by=order_by)


def main():
    arguments = parser.parse_args()

    store, schema, suffix = process_config(arguments)
    rebuild_index(store, schema, suffix, ['pid'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
