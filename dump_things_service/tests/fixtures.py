import sys
from pathlib import Path

import pytest
import yaml

from dump_things_service import config_file_name
from dump_things_service.config import GlobalConfig
from dump_things_service.tests.create_store import (
    create_store,
    pid,
    pid_curated,
    pid_trr,
    test_record,
    test_record_curated,
    test_record_trr,
)

# String representation of curated- and incoming-path
curated = 'curated'
incoming = 'incoming'


# The global configuration file, all collections and
# staging areas share the same directories. All token
# of the same collection share an "incoming_label".
global_config_text = f"""
type: collections
version: 1
collections:
  collection_1:
    default_token: basic_access
    curated: {curated}/collection_1
    incoming: {incoming}/collection_1
  collection_2:
    default_token: basic_access
    curated: {curated}/collection_2
    incoming: {incoming}/collection_2
  collection_3:
    default_token: basic_access
    curated: {curated}/collection_3
  collection_4:
    default_token: basic_access
    curated: {curated}/collection_4
  collection_5:
    default_token: basic_access
    curated: {curated}/collection_5
  collection_6:
    default_token: basic_access
    curated: {curated}/collection_6
  collection_7:
    default_token: basic_access
    curated: {curated}/collection_7
  collection_trr379:
    default_token: basic_access
    curated: {curated}/collection_trr379
    incoming: {incoming}/collection_trr379

tokens:
  basic_access:
    user_id: anonymous
    collections:
      collection_1:
        mode: READ_CURATED
        incoming_label: ''
      collection_2:
        mode: READ_CURATED
        incoming_label: ''
      collection_3:
        mode: READ_CURATED
        incoming_label: ''
      collection_4:
        mode: READ_CURATED
        incoming_label: ''
      collection_5:
        mode: READ_CURATED
        incoming_label: ''
      collection_6:
        mode: READ_CURATED
        incoming_label: ''
      collection_7:
        mode: READ_CURATED
        incoming_label: ''
      collection_trr379:
        mode: READ_CURATED
        incoming_label: ''
  token_1:
    user_id: test_user_1
    collections:
      collection_1:
        mode: WRITE_COLLECTION
        incoming_label: in_token_1
      collection_trr379:
        mode: WRITE_COLLECTION
        incoming_label: in_token_1
  token_1_xxo:
    user_id: test_user_1_read_collection
    collections:
      collection_1:
        mode: READ_COLLECTION
        incoming_label: modes
  token_1_xxx:
    user_id: test_user_1_write_collection
    collections:
      collection_1:
        mode: WRITE_COLLECTION
        incoming_label: modes
  token_1_oxo:
    user_id: test_user_1_read_submissions
    collections:
      collection_1:
        mode: READ_SUBMISSIONS
        incoming_label: modes
  token_1_oxx:
    user_id: test_user_1_write_submissions
    collections:
      collection_1:
        mode: WRITE_SUBMISSIONS
        incoming_label: modes
  token_1_xox:
    user_id: test_user_1_submit
    collections:
      collection_1:
        mode: SUBMIT
        incoming_label: modes
  token_1_oox:
    user_id: test_user_1_submit_only
    collections:
      collection_1:
        mode: SUBMIT_ONLY
        incoming_label: modes
  token_1_oox:
    user_id: test_user_1_submit_only
    collections:
      collection_1:
        mode: SUBMIT_ONLY
        incoming_label: modes
  token_1_xoo:
    user_id: test_user_1_read_curated
    collections:
      collection_1:
        mode: READ_CURATED
        incoming_label: modes
  token_1_ooo:
    user_id: test_user_1_nothing
    collections:
      collection_1:
        mode: NOTHING
        incoming_label: modes
  token_2:
    user_id: test_user_2
    collections:
      collection_2:
        mode: WRITE_COLLECTION
        incoming_label: in_token_2
"""


@pytest.fixture(scope='session')
def dump_stores_simple(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp('dump_store')
    schema_path = Path(__file__).parent / 'testschema.yaml'
    (tmp_path / config_file_name).write_text(global_config_text)

    default_entries = {
        f'collection_{i}': [('Person', pid, test_record)] for i in range(1, 8)
    }
    default_entries['collection_1'].extend(
        [
            ('Person', pid_curated, test_record_curated),
            (
                'Person',
                'abc:mode_test',
                'pid: abc:mode_test\ngiven_name: mode_curated\n',
            ),
        ]
    )
    default_entries['collection_trr379'] = [('Person', pid_trr, test_record_trr)]
    create_store(
        root_dir=tmp_path,
        config=GlobalConfig(**yaml.safe_load(global_config_text)),
        per_collection_info={
            'collection_1': (str(schema_path), 'digest-md5'),
            'collection_2': (str(schema_path), 'digest-md5-p3'),
            'collection_3': (str(schema_path), 'digest-sha1'),
            'collection_4': (str(schema_path), 'digest-sha1-p3'),
            'collection_5': (str(schema_path), 'after-last-colon'),
            'collection_6': (str(schema_path), 'digest-md5-p3-p3'),
            'collection_7': (str(schema_path), 'digest-sha1-p3-p3'),
            'collection_trr379': (
                'https://concepts.trr379.de/s/base/unreleased.yaml',
                'digest-md5',
            ),
        },
        default_entries=default_entries,
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
