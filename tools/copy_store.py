from __future__ import annotations   # noqa: I001 -- the patches have to be imported early

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
    help='rebuild the index of a `record_dir`-source, using the specified SCHEMA.',
    metavar='SCHEMA',
)  # noqa S104



arguments = parser.parse_args()


def main():
    pass

if __name__ == '__main__':
    main()
