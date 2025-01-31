from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient


temp_dir_obj = TemporaryDirectory()
temp_dir = Path(temp_dir_obj.name)
(temp_dir / 'config.yaml').write_text("""
global_store: global
token_stores:
    token1: token1
    token2: token2
"""
)


with patch.dict('os.environ', {'DUMPTHINGS_CONFIG_FILE': str(temp_dir / 'config.yaml')}):
    from ..main import app


client = TestClient(app)


def test_docs():
    pass
