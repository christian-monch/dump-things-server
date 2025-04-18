import sys
from pathlib import Path

import pytest

from dump_things_service.tests.create_store import create_stores

pid = 'abc:some_timee@x.com'
given_name = 'Wolfgang'
test_record = f"""pid: {pid}
given_name: {given_name}
"""

pid_trr = 'trr379:amadeus'
given_name_trr = 'Amadeus'
test_record_trr = f"""pid: {pid_trr}
given_name: {given_name_trr}
"""


@pytest.fixture(scope='session')
def dump_stores_simple(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp('dump_stores')
    schema_path = Path(__file__).parent / 'testschema.yaml'
    create_stores(
        root_dir=tmp_path,
        collection_info={
            'collection_1': (str(schema_path), 'digest-md5'),
            'collection_2': (str(schema_path), 'digest-md5-p3'),
            'collection_3': (str(schema_path), 'digest-sha1'),
            'collection_4': (str(schema_path), 'digest-sha1-p3'),
            'collection_5': (str(schema_path), 'after-last-colon'),
        },
        token_stores=['token_1', 'token_1_xx', 'token_1_xo', 'token_1_ox'],
        default_entries=[('Person', pid, test_record)],
        token_configs={
            'token_1_oo': (False, False),
            'token_1_ox': (False, True),
            'token_1_xo': (True, False),
        },
    )
    create_stores(
        root_dir=tmp_path,
        collection_info={
            'collection_trr379': (
                'https://concepts.trr379.de/s/base/unreleased.yaml',
                'digest-md5',
            ),
        },
        token_stores=['token_1'],
        default_entries=[('Person', pid_trr, test_record_trr)],
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
