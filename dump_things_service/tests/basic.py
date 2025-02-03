import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from .create_store import create_store


temp_dir_obj = TemporaryDirectory()
temp_dir = Path(temp_dir_obj.name)


create_store(
    temp_dir / 'global_store',
    {
        'schema_1': ('https://concepts.trr379.de/s/base/unreleased.yaml', 'digest-md5'),
        'schema_2': ('https://concepts.trr379.de/s/base/unreleased.yaml', 'digest-md5-p3'),
        'schema_3': ('https://concepts.trr379.de/s/base/unreleased.yaml', 'digest-sha1'),
        'schema_4': ('https://concepts.trr379.de/s/base/unreleased.yaml', 'digest-sha1-p3'),
        'schema_5': ('https://concepts.trr379.de/s/base/unreleased.yaml', 'after-last-colon'),
    }
)

create_store(
    temp_dir / 'token1_store',
    {
        'schema_1': ('https://concepts.trr379.de/s/base/unreleased.yaml', 'digest-md5'),
        'schema_2': ('https://concepts.trr379.de/s/base/unreleased.yaml', 'digest-md5-p3'),
        'schema_3': ('https://concepts.trr379.de/s/base/unreleased.yaml', 'digest-sha1'),
        'schema_4': ('https://concepts.trr379.de/s/base/unreleased.yaml', 'digest-sha1-p3'),
        'schema_5': ('https://concepts.trr379.de/s/base/unreleased.yaml', 'after-last-colon'),
    }
)


test_config = f"""
global_store: {str(temp_dir / 'global_store')}
token_stores:
  token1: {str(temp_dir / 'token1_store')}
"""

(temp_dir / 'test_config.yaml').write_text(test_config)


with patch.dict('os.environ', {'DUMPTHINGS_CONFIG_FILE': str(temp_dir / 'test_config.yaml')}):
    from ..main import app


client = TestClient(app)


def test_find():
    for i in range(1, 6):
        response = client.get(f'/schema_{i}/find/1111')
        assert json.loads(response.text) == {'type': 'dltemporal:InstantaneousEvent', 'id': '1111'}
