import sys
from pathlib import Path

import pytest

from dump_things_service.tests.create_store import create_stores

identifier = 'abc:some_timee@x.com'
given_name = 'Wolfgang'
test_record = f"""id: {identifier}
given_name: {given_name}
"""

identifier_trr = 'trr379:amadeus'
given_name_trr = 'Amadeus'
test_record_trr = f"""id: {identifier_trr}
given_name: {given_name_trr}
"""


@pytest.fixture(scope='session')
def dump_stores_simple(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp('dump_stores')
    schema_path = Path(__file__).parent / 'testschema.yaml'
    create_stores(
        root_dir=tmp_path,
        collection_info={
            'store_1': (str(schema_path), 'digest-md5'),
            'store_2': (str(schema_path), 'digest-md5-p3'),
            'store_3': (str(schema_path), 'digest-sha1'),
            'store_4': (str(schema_path), 'digest-sha1-p3'),
            'store_5': (str(schema_path), 'after-last-colon'),
        },
        token_stores=['token_1'],
        default_entries=[('Person', identifier, test_record)],
    )
    create_stores(
        root_dir=tmp_path,
        collection_info={
            'trr379_store': (
                'https://concepts.trr379.de/s/base/unreleased.yaml',
                'digest-md5',
            ),
        },
        token_stores=['token_1'],
        default_entries=[('Person', identifier_trr, test_record_trr)],
    )
    return tmp_path


@pytest.fixture(scope='session')
def fastapi_app_simple(dump_stores_simple):
    old_sys_argv = sys.argv
    sys.argv = ['test-runner', str(dump_stores_simple)]
    from dump_things_service.main import app

    sys.argv = old_sys_argv
    return app, dump_stores_simple


@pytest.fixture(scope='session')
def fastapi_client_simple(fastapi_app_simple):
    from fastapi.testclient import TestClient

    return TestClient(fastapi_app_simple[0]), fastapi_app_simple[1]
