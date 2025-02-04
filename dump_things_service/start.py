import argparse
import logging

import uvicorn

import dump_things_service.shared


parser = argparse.ArgumentParser()
parser.add_argument('--host')
parser.add_argument('--port', type=int)
parser.add_argument('--dev', action='store_true')
parser.add_argument('store', help='The root of the data stores, it should contain a global_store and token_stores.')

arguments = parser.parse_args()

if arguments.dev:
    logging.basicConfig(level=logging.DEBUG)
    default_host= '127.0.0.1'
    default_port = 8000
else:
    default_host = '0.0.0.0'
    default_port = 8000

arguments.host = default_host if arguments.host is None else arguments.host
arguments.port = default_port if arguments.port is None else arguments.port

dump_things_service.shared.arguments = arguments


def main():
    uvicorn.run(
        'dump_things_service.main:app',
        host=arguments.host,
        port=arguments.port,
        reload=arguments.dev,
    )


if __name__ == '__main__':
    main()
