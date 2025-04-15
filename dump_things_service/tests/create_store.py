from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from dump_things_service.storage import (
    MappingMethod,
    config_file_name,
    mapping_functions,
    token_config_file_name,
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

pid = 'abc:some_timee@x.com'
given_name = 'Wolfgang'
test_record = f"""pid: {pid}
given_name: {given_name}
"""

pid_trr = 'trr379:amadeus'
given_name_trr = 'Amadeus'
test_record_trr = f"""pid: {pid_trr}
given_name: {given_name_trr}
"""


def create_stores(
    root_dir: Path,
    collection_info: dict[str, tuple[str, str]],
    token_stores: list[str] | None = None,
    default_entries: list[tuple[str, str, str]] | None = None,
    token_configs: dict[str, tuple[bool, bool]] | None = None,
):
    global_store = root_dir / 'global_store'
    global_store.mkdir(parents=True, exist_ok=True)
    token_store_dir = root_dir / 'token_stores'
    global_store.mkdir(parents=True, exist_ok=True)

    create_store(global_store, collection_info, default_entries)
    token_configs = token_configs or {}
    for token in token_stores or []:
        (token_store_dir / token).mkdir(parents=True, exist_ok=True)
        if token in token_configs:
            config = yaml.dump(
                data=dict(
                    zip(['read_access', 'write_access'], token_configs[token])
                ),
                sort_keys=False,
            )
            (token_store_dir / token / token_config_file_name).write_text(config)

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
        for class_name, pid, record in default_entries or []:
            record_path = (
                collection_dir
                / class_name
                / mapper(
                    pid=pid,
                    suffix='yaml',
                )
            )
            record_path.parent.mkdir(parents=True, exist_ok=True)
            record_path.write_text(record)
