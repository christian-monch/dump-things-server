from __future__ import annotations

from pathlib import Path

from dump_things_service.backends.record_dir import _RecordDirStore

# Path to a local simple test schema
schema_path = Path(__file__).parent.parent.parent / 'tests' / 'testschema.yaml'


def test_add_and_delete_record(tmp_path):
    iri = 'abc.json'

    record_dir_store = _RecordDirStore(
        root=tmp_path,
        pid_mapping_function=lambda pid, suffix: f'{pid}.{suffix}',
        suffix='yaml',
    )

    record_dir_store.build_index(str(schema_path))

    record_dir_store.add_record(
        iri=iri,
        class_name='Object',
        json_object={'pid': 'some-pid'}
    )

    record = record_dir_store.get_record_by_iri(iri=iri)
    assert record is not None

    result = record_dir_store.remove_record(iri=iri)
    assert result is True

    record = record_dir_store.get_record_by_iri(iri=iri)
    assert record is None
