from pathlib import Path

import yaml

from dump_things_service.config import (
    InstanceConfig,
    get_mapping_function_by_name,
)
from dump_things_service.model import get_classes
from dump_things_service.store.model_store import ModelStore

idfx = get_mapping_function_by_name('digest-md5-p3-p3')


def export_tree(
    instance_config: InstanceConfig,
    destination: str,
):
    destination = Path(destination)
    if destination.exists() and not destination.is_dir():
        msg = 'The export_tree destination path must be a directory.'
        raise ValueError(msg)

    destination.mkdir(parents=True, exist_ok=True)
    for collection in instance_config.collections:
        export_collection(
            instance_config,
            collection,
            destination,
        )


def export_collection(
    instance_config: InstanceConfig,
    collection: str,
    destination: Path,
):
    collection_destination = destination / collection
    collection_destination.mkdir(parents=True, exist_ok=True)

    config_content = (
        'type: records\n'
        'version: 1\n'
        f'schema: {instance_config.schemas[collection]}\n'
        'format: yaml\n'
        'idfx: digest-md5-p3-p3\n'
    )

    curated_destination = collection_destination / 'curated'
    curated_destination.mkdir(parents=True, exist_ok=True)
    (curated_destination / '.dumpthings.yaml').write_text(config_content)
    exported_stores = {
        id(instance_config.curated_stores[collection]): curated_destination
    }
    export_classes(instance_config.curated_stores[collection], curated_destination)

    # Determine stores for incoming zones
    zones = {
        label: instance_config.token_stores[token]['collections']
        .get(collection, {})
        .get('store')
        for token, label in instance_config.zones.get(collection, {}).items()
        if instance_config.token_stores[token]['collections']
        .get(collection, {})
        .get('store')
        is not None
    }

    if zones:
        incoming_destination = collection_destination / 'incoming'
        for zone, store in zones.items():
            zone_destination = incoming_destination / zone
            if id(store) in exported_stores:
                # Already exported this store, make `zone_destination` a link
                # to the existing export.
                zone_destination.parent.mkdir(parents=True, exist_ok=True)
                zone_destination.symlink_to(exported_stores[id(store)])
                continue
            exported_stores[id(store)] = zone_destination = (
                collection_destination / 'incoming' / zone
            )
            zone_destination.mkdir(parents=True, exist_ok=True)
            (zone_destination / '.dumpthings.yaml').write_text(config_content)
            export_classes(store, zone_destination)


def export_classes(
    store: ModelStore,
    destination: Path,
):
    class_names = get_classes(store.model)
    for class_name in class_names:
        # We know that pure `Thing` instances are not stored in the store.
        if class_name == 'Thing':
            continue

        record_infos = store.get_objects_of_class(class_name, include_subclasses=False)
        if record_infos:
            class_destination = destination / class_name
            class_destination.mkdir(parents=True, exist_ok=True)
            for record_info in record_infos:
                json_object = record_info.json_object
                instance_destination = class_destination / idfx(
                    json_object['pid'],
                    'yaml',
                )
                instance_destination.parent.mkdir(parents=True, exist_ok=True)
                instance_destination.write_text(
                    yaml.dump(
                        data=json_object,
                        sort_keys=False,
                        allow_unicode=True,
                        default_flow_style=False,
                    )
                )
