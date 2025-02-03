import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from .create_store import create_stores


temp_dir_obj = TemporaryDirectory()
temp_dir = Path(temp_dir_obj.name)


create_stores(
    root_dir=temp_dir,
    collection_info={
        'schema_1': ('https://concepts.trr379.de/s/base/unreleased.yaml', 'digest-md5'),
        'schema_2': ('https://concepts.trr379.de/s/base/unreleased.yaml', 'digest-md5-p3'),
        'schema_3': ('https://concepts.trr379.de/s/base/unreleased.yaml', 'digest-sha1'),
        'schema_4': ('https://concepts.trr379.de/s/base/unreleased.yaml', 'digest-sha1-p3'),
        'schema_5': ('https://concepts.trr379.de/s/base/unreleased.yaml', 'after-last-colon'),
    },
    token_stores=['token_1'],
)


old_sys_argv = sys.argv
sys.argv = ['test', str(temp_dir)]
from ..main import app
sys.argv = old_sys_argv

client = TestClient(app)


def test_search_by_id():
    for i in range(1, 6):
        response = client.get(f'/schema_{i}/record/1111')
        assert json.loads(response.text) == {'type': 'dltemporal:InstantaneousEvent', 'id': '1111'}


def test_store_record():
    for i in range(1, 6):
        response = client.post(
            f'/schema_{i}/record/InstantaneousEvent',
            headers={'x-dumpthings-token': 'token_1'},
            data={'id': 'aaaa'}
        )
        assert response.status_code == 200

    for i in range(1, 6):
        response = client.get(f'/schema_{i}/record/aaaa')
        assert response.status_code == 200


def test_global_store_fails():
    for i in range(1, 6):
        response = client.post(
            f'/schema_{i}/record/InstantaneousEvent',
            data={'id': 'aaaa'}
        )
        assert response.status_code == 422
