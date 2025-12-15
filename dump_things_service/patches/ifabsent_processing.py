""" Monkeypatch for linkml.generators.common.ifabsent_processor.IfAbsentProcessor

Patches the ifabsent-processor to not use namespace objects. Those are not
generated in the pydantic code generator.
"""
import logging
from importlib import import_module


logger = logging.getLogger('dump_things_service')


def patched_uri_for(self, s: str) -> str:
    uri = str(self.schema_view.namespaces().uri_for(s))
    curie = self.schema_view.namespaces().curie_for(uri, True)
    return f"'{curie}'" if curie else self._strval(uri)


logger.info('patching linkml.generators.common.ifabsent_processor.IfAbsentProcessor._uri_for')

cls = import_module('linkml.generators.common.ifabsent_processor')
cls.IfAbsentProcessor._uri_for = patched_uri_for
