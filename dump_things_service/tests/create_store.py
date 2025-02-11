from __future__ import annotations

from typing import TYPE_CHECKING

from dump_things_service.storage import (
    MappingMethod,
    config_file_name,
    mapping_functions,
)

if TYPE_CHECKING:
    from pathlib import Path

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

identifier = 'abc:some_timee@x.com'
given_name = 'Wolfgang'
test_record = f"""id: {identifier}
given_name: {given_name}
"""

identifier_trr = 'trr379:amadeus'
given_name_trr = 'Amadeus'
test_record_trr = f"""id: {identifier_trr}
given_name: {given_name_trr}
"""


def create_stores(
    root_dir: Path,
    collection_info: dict[str, tuple[str, str]],
    token_stores: list[str] | None = None,
    default_entries: list[tuple[str, str, str]] | None = None,
):
    global_store = root_dir / 'global_store'
    global_store.mkdir(parents=True, exist_ok=True)
    token_store_dir = root_dir / 'token_stores'
    global_store.mkdir(parents=True, exist_ok=True)

    create_store(global_store, collection_info, default_entries)
    for token in token_stores or []:
        (token_store_dir / token).mkdir(parents=True, exist_ok=True)


def create_store(
    temp_dir: Path,
    collection_info: dict[str, tuple[str, str]],
    default_entries: list[tuple[str, str, str]] | None = None,
):
    global_config_file = temp_dir / config_file_name
    global_config_file.parent.mkdir(parents=True, exist_ok=True)
    global_config_file.write_text(global_config)

    for collection, (schema_url, mapping_function) in collection_info.items():
        # Create a collection directory
        collection_dir = temp_dir / collection
        collection_dir.mkdir(parents=True, exist_ok=True)

        # Add the collection level config file
        collection_config_file = collection_dir / config_file_name
        collection_config_file.write_text(
            collection_config_template.format(
                schema=schema_url, mapping_function=mapping_function
            )
        )

        # Add default entries
        mapper = mapping_functions[MappingMethod(mapping_function)]
        for class_name, identifier, record in default_entries or []:
            record_path = (
                collection_dir
                / class_name
                / mapper(
                    identifier=identifier,
                    data=record,
                    suffix='yaml',
                )
            )
            record_path.parent.mkdir(parents=True, exist_ok=True)
            record_path.write_text(record)
