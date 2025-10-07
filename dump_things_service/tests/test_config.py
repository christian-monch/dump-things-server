
import pytest
import yaml
from pydantic import ValidationError
from yaml.scanner import ScannerError

from dump_things_service.config import (
    ConfigError,
    GlobalConfig,
    process_config,
    process_config_object, get_config,
)


def test_scanner_error_detection(tmp_path):
    config_file_path = tmp_path / 'config.yaml'
    config_file_path.write_text('type: col: le\n:xxx:')
    global_dict = {}
    with pytest.raises(ConfigError) as e:
        process_config(tmp_path, config_file_path, [], global_dict)
    assert isinstance(e.value.__cause__, ScannerError)


def test_structure_error_detection(tmp_path):
    config_file_path = tmp_path / 'config.yaml'
    config_file_path.write_text('type: colle\n')
    global_dict = {}
    with pytest.raises(ConfigError) as e:
        process_config(tmp_path, config_file_path, [], global_dict)
    assert isinstance(e.value.__cause__, ValidationError)


def test_missing_incoming_detection(tmp_path):
    config_object = GlobalConfig(
        **yaml.load(
            """
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
    """,
            Loader=yaml.SafeLoader,
        )
    )

    global_dict = {}
    with pytest.raises(ConfigError):
        process_config_object(tmp_path, config_object, [], global_dict)


def test_submission_tags_handling(dump_stores_simple):
    config_object = GlobalConfig(
        **yaml.load(
            """
type: collections
version: 1
collections:
  collection_1:
    default_token: basic_access
    curated: curated/in_token_1
    incoming: contributions
    submission_tags:
      submitter_id_tag: no_default_id_tag
      submission_time_tag: no_default_time_tag
  collection_2:
    default_token: basic_access
    curated: curated/collection_2
    incoming: contributions
tokens:
  basic_access:
    user_id: anonymous
    collections:
      collection_1:
        mode: WRITE_COLLECTION
        incoming_label: incoming_anonymous
      collection_2:
        mode: WRITE_COLLECTION
        incoming_label: incoming_anonymous
    """,
            Loader=yaml.SafeLoader,
        )
    )

    global_dict = {}
    config = process_config_object(dump_stores_simple, config_object, [], global_dict)
    # Check for specified tags in collection `collection_1`
    assert config.collections['collection_1'].submission_tags.submission_time_tag == 'no_default_time_tag'
    assert config.collections['collection_1'].submission_tags.submitter_id_tag == 'no_default_id_tag'
    # Check for default tags in collection `collection_2`
    assert config.collections['collection_2'].submission_tags.submission_time_tag == 'http://semanticscience.org/resource/SIO_001083'
    assert config.collections['collection_2'].submission_tags.submitter_id_tag == 'http://purl.obolibrary.org/obo/NCIT_C54269'
