from __future__ import annotations

import argparse
import logging

logger = logging.getLogger('dump_things_copy')


parser = argparse.ArgumentParser()
parser.add_argument(
    '--from',
    help='specify the backend and location from which the records should be read. '
    'The format is: `<backend>:<path>. Supported backends are: "sqlite", and '
    '"record_dir".',
)
parser.add_argument(
    '--to',
    help='specify the backend and location in which the records should be stored. '
    'The format is: `<backend>:<path>. Supported backends are: "sqlite", and '
    '"record_dir".',
)
parser.add_argument(
    '--rebuild-source-index',
    help='rebuild the index of a `record_dir`-source, using the specified SCHEMA. '
    'This is required if the source has no persistent index, i.e., if the source '
    'is a `record_dir`-backend. It is useful, if files have been added or removed '
    'manually from a `record_dir`-backend.',
    metavar='SCHEMA',
)


arguments = parser.parse_args()


def main():
    pass


if __name__ == '__main__':
    main()
