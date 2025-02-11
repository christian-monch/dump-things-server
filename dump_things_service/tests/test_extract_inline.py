import pytest  # noqa F401

from . import HTTP_200_OK
from .fixtures import fastapi_client_simple
from dump_things_service import JSON
from dump_things_service.storage import (
    Storage,
    TokenStorage,
)

inlined_json_record = {
    'id': 'trr379:root_element',
    'schema_type': 'dlsocial:Person',
    'given_name': 'Grandfather',
    'relations': {
        'trr379:child_element_1': {
            'id': 'trr379:child_element_1',
            'schema_type': 'dlsocial:Person',
            'given_name': 'Father',
            'relations': {
                'trr379:grand_child_element': {
                    'id': 'trr379:grand_child_element',
                    'schema_type': 'dlsocial:Person',
                    'given_name': 'Son',
                },
            },
        },
        'trr379:child_element_2': {
            'id': 'trr379:child_element_2',
            'schema_type': 'dlsocial:Person',
            'given_name': 'Aunt',
        },
    },
}

tree = (
    ('trr379:root_element', ('trr379:child_element_1', 'trr379:child_element_2')),
    ('trr379:child_element_1', ('trr379:grand_child_element',)),
    ('trr379:child_element_2', ()),
    ('trr379:grand_child_element', ()),
)


def test_inline_extraction_locally(dump_stores_simple):
    root = dump_stores_simple

    store = TokenStorage(
        root / 'token_stores' / 'token_1',
        Storage(root / 'global_store')
    )
    records = store.extract_inlined(inlined_json_record)
    _check_result(records, tree)


def _check_result(
    records: list[JSON],
    tree: tuple[tuple[str, tuple[str, ...]]],
):
    def get_record_by_id(record_id: str):
        for record in records:
            if record['id'] == record_id:
                return record
        return None

    for record_id, linked_ids in tree:
        record = get_record_by_id(record_id)
        import sys
        print('RECORD:', record, file=sys.stderr, flush=True)
        if 'relations' in record:
            assert len(record['relations']) == len(linked_ids)
        for linked_id in linked_ids:
            print('CHECKING:', linked_id, file=sys.stderr, flush=True)
            assert record['relations'][linked_id] == {'id': linked_id}


def test_inline_extraction_on_service(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Deposit JSON record
    response = test_client.post(
        '/trr379_store/record/Person',
        headers={'x-dumpthings-token': 'token_1'},
        json=inlined_json_record,
    )
    assert response.status_code == HTTP_200_OK

    # Expect records with no inlined data but minimal `relations`-entries
    records = []
    for record_id in (entry[0] for entry in tree):
        response = test_client.get(
            f'/trr379_store/record?id={record_id}',
            headers={'x-dumpthings-token': 'token_1'},
        )
        assert response.status_code == HTTP_200_OK
        records.append(response.json())
    _check_result(records, tree)
