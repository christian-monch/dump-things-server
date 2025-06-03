from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from dump_things_service.config import (
    CollectionConfig,
    GlobalConfig,
    MappingMethod,
    config_file_name,
    mapping_functions,
)

if TYPE_CHECKING:
    from pathlib import Path


collection_config_template = """type: records
version: 1
schema: {schema}
format: yaml
idfx: {mapping_function}
"""

pid = 'abc:some_timee@x.com'
given_name = 'WolfgangÖÄß'
test_record = f"""pid: {pid}
given_name: {given_name}
"""

pid_trr = 'trr379:amadeus'
given_name_trr = 'AmadeusÜÄß'
test_record_trr = f"""pid: {pid_trr}
given_name: {given_name_trr}
"""

pid_curated = 'abc:curated'
given_name_curated = 'curated'
test_record_curated = f"""pid: {pid_curated}
given_name: {given_name_curated}
"""

faulty_yaml = ': : -: : :'


def create_store(
    root_dir: Path,
    config: GlobalConfig,
    per_collection_info: dict[str, tuple[str, str]],
    default_entries: dict[str, list[tuple[str, str, str]]] | None = None,
):
    # Create the global config file
    config_text = yaml.safe_dump(
        config.model_dump(mode='json', exclude_none=True),
        allow_unicode=True,
        sort_keys=False,
    )
    with open(root_dir / config_file_name, 'w') as f:
        f.write(config_text)

    # Create all collection directories
    for collection_name, collection_config in config.collections.items():
        create_collection(
            root_dir=root_dir,
            collection_config=collection_config,
            schema_url=per_collection_info[collection_name][0],
            mapping_function=per_collection_info[collection_name][1],
            default_entries=(default_entries or {}).get(collection_name),
        )


def create_collection(
    root_dir: Path,
    collection_config: CollectionConfig,
    schema_url: str,
    mapping_function: str,
    default_entries: list[tuple[str, str, str]] | None = None,
):
    # Create a directory for the curated collection
    curated_dir = root_dir / collection_config.curated
    if not curated_dir.is_absolute():
        msg = f'Curated collection path not absolute: {curated_dir}'
        raise ValueError(msg)
    if curated_dir.exists():
        if not curated_dir.is_dir():
            msg = f'Curated collection path not a directory: {curated_dir}'
            raise ValueError(msg)
    else:
        curated_dir.mkdir(parents=True, exist_ok=True)

    # Add the collection level config file
    collection_config_file = curated_dir / config_file_name
    collection_config_file.write_text(
        collection_config_template.format(
            schema=schema_url, mapping_function=mapping_function
        )
    )

    # Add default entries
    mapper = mapping_functions[MappingMethod(mapping_function)]
    for class_name, pid, record in default_entries or []:
        record_path = (
            curated_dir
            / class_name
            / mapper(
                pid=pid,
                suffix='yaml',
            )
        )
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text(record)

    # Add some faulty entries to check error handling while reading collections
    (curated_dir / 'faulty-file.yaml').write_text(faulty_yaml)

    # Add an erroneous yaml file with a non-yaml extension
    (curated_dir / 'faulty-file.txt').write_text(faulty_yaml)
