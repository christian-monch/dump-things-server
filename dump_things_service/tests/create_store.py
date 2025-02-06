from __future__ import annotations

import sys
from pathlib import Path

import pytest

from ..storage import (
    MappingMethod,
    mapping_functions,
    config_file_name,
)


global_config = """
type: collections
version: 1
"""


collection_config_template = """
type: records
version: 1
schema: {schema}
format: yaml
idfx: {mapping_function}
"""

identifier = 'https://www.example.com/Persons/some_timee@x.com'
given_name = 'Wolfgang'

test_record = f"""id: "{identifier}"
given_name: Wolfgang
"""


def create_stores(
    root_dir: Path,
    collection_info: dict[str, tuple[str, str]],
    token_stores: list[str] | None = None,
):
    global_store = root_dir / 'global_store'
    global_store.mkdir()
    token_store_dir = root_dir / 'token_stores'
    token_store_dir.mkdir()

    create_store(global_store, collection_info)
    for token in token_stores or []:
        (token_store_dir / token).mkdir()


def create_store(
    temp_dir: Path,
    collection_info: dict[str, tuple[str, str]]
):
    global_config_file = temp_dir / config_file_name
    global_config_file.parent.mkdir(parents=True, exist_ok=True)
    global_config_file.write_text(global_config)

    for label, (schema_url, mapping_function) in collection_info.items():
        # Create a collection directory
        collection_dir = temp_dir / label
        collection_dir.mkdir()

        # Add the collection level config file
        collection_config_file = collection_dir / config_file_name
        collection_config_file.write_text(
            collection_config_template.format(
                schema=schema_url,
                mapping_function=mapping_function
            )
        )

        # Add a test record
        mapping_function = mapping_functions[MappingMethod(mapping_function)]
        record_path = collection_dir / 'Person' / mapping_function(
            identifier=identifier,
            data=test_record,
            suffix='yaml'
        )
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text(test_record)


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
    )
    return tmp_path


@pytest.fixture(scope='session')
def fastapi_app_simple(dump_stores_simple):
    old_sys_argv = sys.argv
    sys.argv = ['test-runner', str(dump_stores_simple)]
    from ..main import app
    sys.argv = old_sys_argv
    return app, dump_stores_simple


@pytest.fixture(scope='session')
def fastapi_client_simple(fastapi_app_simple):
    from fastapi.testclient import TestClient
    return TestClient(fastapi_app_simple[0]), fastapi_app_simple[1]


@pytest.fixture(scope='session')
def dump_stores(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp('dump_stores')
    create_stores(
        root_dir=tmp_path,
        collection_info={
            'store_1': ('https://concepts.trr379.de/s/base/unreleased.yaml', 'digest-md5'),
        },
        token_stores=['token_1'],
    )
    return tmp_path


@pytest.fixture(scope='session')
def fastapi_app(dump_stores):
    old_sys_argv = sys.argv
    sys.argv = ['test-runner', str(dump_stores)]
    from ..main import app
    sys.argv = old_sys_argv
    return app, dump_stores


@pytest.fixture(scope='session')
def fastapi_client(fastapi_app):
    from fastapi.testclient import TestClient
    return TestClient(fastapi_app[0]), fastapi_app[1]
