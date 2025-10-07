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

# Path to a local simple test schema
schema_path = Path(__file__).parent / 'testschema.yaml'


# The global configuration file, all collections and
# staging areas share the same directories. All tokens
# of the same collection share an "incoming_label".
global_config_text = f"""
type: collections
version: 1
collections:
  collection_1:
    default_token: basic_access
    curated: {curated}/in_token_1
    incoming: {incoming}
    backend:
      type: record_dir+stl
    auth_sources:
      - type: config
    submission_tags:
      submitter_id_tag: oxo:NCIT_C54269
      submission_time_tag: https://time
  collection_2:
    default_token: basic_access
    curated: {curated}/collection_2
    incoming: incoming_2
    backend:
      type: record_dir+stl
  collection_3:
    default_token: basic_access
    curated: {curated}/collection_3
    incoming: incoming_3
    backend:
      type: record_dir+stl
  collection_4:
    default_token: basic_access
    curated: {curated}/collection_4
    incoming: incoming_4
    backend:
      type: record_dir+stl
  collection_5:
    default_token: basic_access
    curated: {curated}/collection_5
    incoming: incoming_5
    backend:
      type: record_dir+stl
  collection_6:
    default_token: basic_access
    curated: {curated}/collection_6
    incoming: incoming_6
    backend:
      type: record_dir+stl
  collection_7:
    default_token: basic_access
    curated: {curated}/collection_7
    incoming: incoming_7
    backend:
      type: record_dir+stl
  collection_8:
    default_token: basic_access
    curated: {curated}/collection_8
    incoming: incoming_8
    backend:
      type: sqlite
      schema: {schema_path}
  collection_dlflatsocial-1:
    default_token: basic_access
    curated: {curated}/collection_dlflatsocial-1
    incoming: {incoming}/collection_dlflatsocial-1
    backend:
      type: record_dir+stl
  collection_dlflatsocial-2:
    default_token: basic_access
    curated: {curated}/collection_dlflatsocial-2
    incoming: {incoming}/collection_dlflatsocial-2
    backend:
      type: sqlite
      schema: https://concepts.datalad.org/s/flat-social/unreleased.yaml

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
      collection_8:
        mode: READ_CURATED
        incoming_label: ''
      collection_dlflatsocial-1:
        mode: READ_CURATED
        incoming_label: ''
      collection_dlflatsocial-2:
        mode: READ_CURATED
        incoming_label: ''
  cmo-33b726a7e2b9eaf1f8f124049822ade31cb6516a4d8221634b01d13d793bfe16:
    hashed: True
    user_id: cmo
    collections:
      collection_1:
        mode: WRITE_COLLECTION
        incoming_label: cmo
  # The plaintext of the following is `token-1`:
  token-6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b:
    hashed: True
    user_id: test_user_1
    collections:
      collection_1:
        mode: WRITE_COLLECTION
        incoming_label: in_token_1
      collection_dlflatsocial-1:
        mode: WRITE_COLLECTION
        incoming_label: in_token_1
      collection_dlflatsocial-2:
        mode: WRITE_COLLECTION
        incoming_label: in_token_1
  token_1_xxooo:
    user_id: test_user_1_read_collection
    collections:
      collection_1:
        mode: READ_COLLECTION
        incoming_label: modes
  token_1_xxxoo:
    user_id: test_user_1_write_collection
    collections:
      collection_1:
        mode: WRITE_COLLECTION
        incoming_label: modes
  token_1_oxooo:
    user_id: test_user_1_read_submissions
    collections:
      collection_1:
        mode: READ_SUBMISSIONS
        incoming_label: modes
  token_1_oxxoo:
    user_id: test_user_1_write_submissions
    collections:
      collection_1:
        mode: WRITE_SUBMISSIONS
        incoming_label: modes
  token_1_xoxoo:
    user_id: test_user_1_submit
    collections:
      collection_1:
        mode: SUBMIT
        incoming_label: modes
  token_1_ooxoo:
    user_id: test_user_1_submit_only
    collections:
      collection_1:
        mode: SUBMIT_ONLY
        incoming_label: modes
  token_1_ooxoo:
    user_id: test_user_1_submit_only
    collections:
      collection_1:
        mode: SUBMIT_ONLY
        incoming_label: modes
  token_1_xoooo:
    user_id: test_user_1_read_curated
    collections:
      collection_1:
        mode: READ_CURATED
        incoming_label: modes
  token_1_ooooo:
    user_id: test_user_1_nothing
    collections:
      collection_1:
        mode: NOTHING
        incoming_label: modes
  token_1_xxxxx:
    user_id: test_user_1_curated
    collections:
      collection_1:
        mode: CURATOR
        incoming_label: modes
      collection_8:
        mode: CURATOR
        incoming_label: modes
  token_admin:
    user_id: test_admin
    collections:
      collection_1:
        mode: CURATOR
        incoming_label: admin_1
      collection_2:
        mode: CURATOR
        incoming_label: admin_2
      collection_3:
        mode: CURATOR
        incoming_label: admin_3
      collection_4:
        mode: CURATOR
        incoming_label: admin_4
      collection_5:
        mode: CURATOR
        incoming_label: admin_common
      collection_6:
        mode: CURATOR
        incoming_label: admin_common
      collection_7:
        mode: CURATOR
        incoming_label: admin_common
      collection_8:
        mode: CURATOR
        incoming_label: admin_common
  token-2:
    user_id: test_user_2
    collections:
      collection_2:
        mode: WRITE_COLLECTION
        incoming_label: in_token-2
  token-8:
    user_id: test_user_8
    collections:
      collection_8:
        mode: WRITE_COLLECTION
        incoming_label: test_user_8
"""


@pytest.fixture(scope='session')
def dump_stores_simple(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp('dump_store')
    (tmp_path / config_file_name).write_text(global_config_text)

    default_entries = {
        f'collection_{i}': [('Person', pid, test_record)] for i in range(1, 9)
    }
    for collection_id in (1, 8):
        default_entries[f'collection_{collection_id}'].extend(
            [
                ('Person', pid_curated, test_record_curated),
                (
                    'Person',
                    'abc:mode_test',
                    'pid: abc:mode_test\ngiven_name: mode_curated\nschema_type: abc:Person\n',
                ),
            ]
        )
    default_entries['collection_dlflatsocial-1'] = [('Person', pid_trr, test_record_trr)]
    default_entries['collection_dlflatsocial-2'] = [('Person', pid_trr, test_record_trr)]
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
            'collection_8': (str(schema_path), 'digest-md5'),
            'collection_dlflatsocial-1': (
                'https://concepts.datalad.org/s/flat-social/unreleased.yaml',
                'digest-md5',
            ),
            'collection_dlflatsocial-2': (
                'https://concepts.datalad.org/s/flat-social/unreleased.yaml',
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
