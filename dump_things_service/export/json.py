import json
import sys
from pathlib import Path
from typing import TextIO

from dump_things_service.config import InstanceConfig
from dump_things_service.lazy_list import LazyList
from dump_things_service.model import get_classes
from dump_things_service.store.model_store import ModelStore

level_width = 2


# The _lookahead function is taken from:
# https://stackoverflow.com/questions/1630320/what-is-the-pythonic-way-to-detect-the-last-element-in-a-for-loop
# with small changes
def _lookahead(iterable):
    """Pass through all values from the given iterable, augmented by the
    information if there are more values to come after the current one
    (True), or if it is the last value (False).
    """
    # Get an iterator and pull the first value.
    it = iter(iterable)
    try:
        last = next(it)
    except StopIteration:
        return
    # Run the iterator to exhaustion (starting from the second value).
    for val in it:
        # Report the *previous* value (more to come).
        yield last, False
        last = val
    # Report the last value.
    yield last, True


def export_json(
    instance_config: InstanceConfig,
    destination: str,
):
    if destination == '-':
        output = sys.stdout
    else:
        output = Path(destination).open('wt', encoding='utf-8')  # noqa: SIM115

    output.write('{\n')
    for collection, is_last in _lookahead(instance_config.collections):
        output.write(f'{level_width * " "}"{collection}": {{\n')
        export_collection(instance_config, collection, 2 * level_width, output)
        if is_last:
            output.write(f'\n{level_width * " "}}}\n')
        else:
            output.write(f'\n{level_width * " "}}},\n')
    output.write('}\n')


def export_collection(
    instance_config: InstanceConfig,
    collection: str,
    indent: int,
    output: TextIO,
):
    output.write(f'{indent * " "}"schema": "{instance_config.schemas[collection]}",\n')
    output.write(f'{indent * " "}"curated": {{\n')
    append_classes(
        instance_config.curated_stores[collection], indent + level_width, output
    )
    output.write(f'\n{indent * " "}}}')

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
        # Put a comma between "curated" and "incoming".
        output.write(f',\n{indent * " "}"incoming": {{\n')
        indent_zone = indent + level_width
        indent_classes = indent_zone + level_width
        for (zone, store), is_last in _lookahead(zones.items()):
            output.write(f'{indent_zone * " "}"{zone}": {{\n')
            append_classes(store, indent_classes, output)
            if is_last:
                output.write(f'\n{(indent + level_width) * " "}}}')
            else:
                output.write(f'\n{(indent + level_width) * " "}}},\n')

        # End the "incoming" dictionary
        output.write(f'\n{indent * " "}}}')


def append_classes(
    store: ModelStore,
    indent: int,
    output: TextIO,
):
    """Append instances of all classes to the file"""
    class_names = get_classes(store.model)

    first = True
    for class_name in class_names:
        # We know that pure `Thing` instances are not stored in the store.
        if class_name == 'Thing':
            continue

        class_instances = store.get_objects_of_class(
            class_name, include_subclasses=False
        )
        if class_instances:
            if not first:
                output.write(',\n')
            first = False
            output.write(f'{indent * " "}"{class_name}": [\n')
            append_instances(
                class_instances,
                output,
                indent + level_width,
            )
            output.write(f'\n{indent * " "}]')


def append_instances(
    instances: LazyList,
    output: TextIO,
    indent: int,
):
    for instance, is_last in _lookahead(instances):
        json_string = json.dumps(instance.json_object, ensure_ascii=False)
        output.write(f'{(indent + level_width) * " "}{json_string}')
        if not is_last:
            output.write(',\n')
