from __future__ import annotations

from dump_things_service.backends.record_dir_index import RecordDirIndex


def test_add_and_delete_entry(tmp_path):
    iri = 'abc:this-is-an-iri'

    record_dir_index = RecordDirIndex(tmp_path, 'yaml')
    record_dir_index.add_iri_info(
        iri,
        'Object',
        '/root/data/something',
        'a1',
    )
    entry = record_dir_index.get_info_for_iri(iri)
    assert entry is not None

    result = record_dir_index.remove_iri_info(iri)
    assert result is True

    entry = record_dir_index.get_info_for_iri(iri)
    assert entry is None

    result = record_dir_index.remove_iri_info(iri)
    assert result is False
