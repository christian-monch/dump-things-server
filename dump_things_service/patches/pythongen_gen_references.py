import logging
from collections import defaultdict
from graphlib import TopologicalSorter
from importlib import import_module

from linkml_runtime.utils.formatutils import camelcase


logger = logging.getLogger('dump_things_service')


def patched_gen_references(self) -> str:
    """Generate python type declarations for all identifiers (primary keys)"""
    rval = dict()
    graph = defaultdict(set)
    for cls in self._sort_classes(self.schema.classes.values()):
        if not cls.imported_from:
            pkeys = self.primary_keys_for(cls)
            if pkeys:
                for pk in pkeys:
                    classname = camelcase(cls.name) + camelcase(self.aliased_slot_name(pk))
                    # If we've got a parent slot and the range of the parent is the range of the child, the
                    # child slot is a subclass of the parent.  Otherwise, the child range has been overridden,
                    # so the inheritance chain has been broken
                    parent_pk = self.class_identifier(cls.is_a) if cls.is_a else None
                    parent_pk_slot = self.schema.slots[parent_pk] if parent_pk else None
                    pk_slot = self.schema.slots[pk]
                    if parent_pk_slot and (parent_pk_slot.name == pk or pk_slot.range == parent_pk_slot.range):
                        parents = self.class_identifier_path(cls.is_a, False)
                    else:
                        parents = self.slot_range_path(pk_slot)
                    parent_cls = (
                        "extended_" + parents[-1] if parents[-1] in ["str", "float", "int"] else parents[-1]
                    )
                    rval[classname] = f"class {classname}({parent_cls}):\n\tpass"
                    graph[classname].add(parent_cls)

                    break  # We only do the first primary key
    return "\n\n\n".join(
        rval[name]
        for name in TopologicalSorter(graph).static_order()
        if name in rval
    )


logger.info('patching linkml.generators.pythongen.PythonGenerator.gen_references')

cls = import_module('linkml.generators.pythongen')
cls.PythonGenerator.gen_references = patched_gen_references
