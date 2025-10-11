import sys
from argparse import ArgumentParser

# Patch linkml
from dump_things_service.patches import enabled

from linkml_runtime.utils.schemaview import SchemaView
from linkml_runtime.utils.yamlutils import as_yaml

parser = ArgumentParser(
    prog='Create a static schema with all imported schemas integrated',
)
parser.add_argument(
    'schema',
    help='File containing a schema definition'
)


def update_uris_for_elements(
        all_elements: dict,
        attribute_name: str,
        prefix_index: dict
):
    for name, info in all_elements.items():
        uri = getattr(info, attribute_name)
        if uri is None:
            source = info.from_schema + '/'
            if source in prefix_index:
                source = prefix_index[source] + ':'
            uri = source + name
            setattr(info, attribute_name, uri)


def update_uris(schema_view: SchemaView):
    """ Update element-defining URIs to the original element source

    Element-defining URIs (e.g., slot_uri, class_uri) are by default set to
    the schema in which the element is defined. In this case, that would be the
    root-schema of the merged schema. The merged schema would then contain different
    element-defining URIs than the individual schemas that were merged. That
    means that records that are based on the individual schemas would not be
    valid in the merged schema.

    This function updates the element-defining URIs to the original source.
    """
    prefix_index = {
        p.prefix_reference: p.prefix_prefix
        for p in schema_view.schema.prefixes.values()
    }
    update_uris_for_elements(schema_view.schema.slots, 'slot_uri', prefix_index)
    update_uris_for_elements(schema_view.schema.types, 'uri', prefix_index)
    update_uris_for_elements(schema_view.schema.enums, 'enum_uri', prefix_index)
    update_uris_for_elements(schema_view.schema.classes, 'class_uri', prefix_index)


def main():
    args = parser.parse_args()

    schema_view = SchemaView(
        schema=args.schema,
        importmap=None,
        merge_imports=True,
    )

    update_uris(schema_view)
    print(as_yaml(schema_view.schema))
    return 0


if __name__ == '__main__':
    sys.exit(main())
