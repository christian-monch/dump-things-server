from importlib import reload
from pathlib import Path

import linkml
import linkml.generators.common.ifabsent_processor as if_abs_proc

import dump_things_service.patches.ifabsent_processing


# Path to a local simple test schema
schema_dir = Path(__file__).parent / 'assets'


def _original_uri_for(self, s: str) -> str:
    uri = str(self.schema_view.namespaces().uri_for(s))
    return self.schema_view.namespaces().curie_for(uri, True, True) or self._strval(uri)


def test_ifabsent_patch():

    # Patch in the faulty, original code and check for its result
    if_abs_proc.IfAbsentProcessor._uri_for = _original_uri_for
    gen1 = linkml.generators.PydanticGenerator(str(schema_dir / 'schema-ifabsent-error.yaml'))
    x = gen1.serialize()
    assert 'default=XSD["04fa4r544"]' in x

    # Apply the patch
    reload(dump_things_service.patches.ifabsent_processing)

    # Check for proper code generation
    gen2 = linkml.generators.PydanticGenerator(str(schema_dir / 'schema-ifabsent-error.yaml'))
    y = gen2.serialize()
    assert 'XSD' not in y
