# The tests below require patches

from pathlib import Path

from dump_things_service.model import (
    get_model_for_schema,
    get_schema_model_for_schema,
)

# Path to a local simple test schema
schema_dir = Path(__file__).parent / 'assets'


def test_gen_pydantic():
    get_model_for_schema(str(schema_dir / 'schema-merged.yaml'))


def test_gen_python():
    get_schema_model_for_schema(str(schema_dir / 'schema-merged.yaml'))
