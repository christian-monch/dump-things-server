from __future__ import annotations

from pathlib import Path

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


test_record = """type: dltemporal:InstantaneousEvent
id: '1111'
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
        create_store(token_store_dir / token, collection_info)


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
        record_path = collection_dir / 'InstantaneousEvent' / mapping_function(
            identifier='1111',
            data=test_record,
            suffix='yaml'
        )
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text(test_record)
