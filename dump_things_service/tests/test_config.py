from pathlib import Path

import pytest
import yaml
from fastapi import HTTPException
from pydantic import ValidationError
from yaml.scanner import ScannerError

from dump_things_service.config import (
    ConfigError,
    GlobalConfig,
    get_token_store,
    get_zone,
    process_config,
    process_config_object,
)
from dump_things_service.tests.create_store import create_store


def test_scanner_error_detection(tmp_path):
    config_file_path = tmp_path / 'config.yaml'
    config_file_path.write_text('type: col: le\n:xxx:')
    global_dict = {}
    with pytest.raises(ConfigError) as e:
        process_config(tmp_path, config_file_path, global_dict)
    assert isinstance(e.value.__cause__, ScannerError)


def test_structure_error_detection(tmp_path):
    config_file_path = tmp_path / 'config.yaml'
    config_file_path.write_text('type: colle\n')
    global_dict = {}
    with pytest.raises(ConfigError) as e:
        process_config(tmp_path, config_file_path, global_dict)
    assert isinstance(e.value.__cause__, ValidationError)


def test_missing_incoming_detection(tmp_path):
    schema_path = Path(__file__).parent / 'testschema.yaml'
    config_object = GlobalConfig(**yaml.load("""
type: collections
version: 1
collections:
  collection_1:
    default_token: basic_access
    curated: curated/collection_1

tokens:
  basic_access:
    user_id: anonymous
    collections:
      collection_1:
        mode: WRITE_COLLECTION
        incoming_label: incoming_anonymous
    """, Loader=yaml.SafeLoader))

    create_store(
        root_dir=tmp_path,
        config=config_object,
        per_collection_info={
            'collection_1': (str(schema_path), 'digest-md5'),
        },
    )

    global_dict = {}
    instance_config = process_config_object(tmp_path, config_object, global_dict)
    with pytest.raises(HTTPException):
        get_token_store(instance_config, 'collection_1', 'basic_access')
    with pytest.raises(HTTPException):
        get_zone(instance_config, 'collection_1', 'basic_access')
