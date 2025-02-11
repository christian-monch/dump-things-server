import pytest  # noqa F401

from . import HTTP_200_OK

inlined_json_record = {
    'id': 'trr379:root_element',
    'schema_type': 'dlsocial:Person',
    'given_name': 'Grandfather',
    'relations' : {
        'trr379:child_element': {
            'id': 'trr379:child_element',
            'schema_type': 'dlsocial:Person',
            'given_name': 'Father',
            'relations': {
                'trr379:grand_child_element': {
                    'id': 'trr379:grand_child_element',
                    'schema_type': 'dlsocial:Person',
                    'given_name': 'Son',
                }
            }
        }
    }
}


def test_inline_extraction(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Deposit JSON record
    response = test_client.post(
        f'/trr379_store/record/Person',
        headers={'x-dumpthings-token': 'token_1'},
        json=inlined_json_record
    )
    assert response.status_code == HTTP_200_OK

    # Expect three records with no inlined data but links to the ids
    for record_id, linked_id in (
        ('trr379:root_element', 'trr379:child_element'),
        ('trr379:child_element', 'trr379:grand_child_element'),
        ('trr379:grand_child_element', None),
    ):
        response = test_client.get(
            f'/trr379_store/record?id={record_id}',
            headers={'x-dumpthings-token': 'token_1'},
        )
        assert response.status_code == HTTP_200_OK
        record = response.json()
        if linked_id:
            assert linked_id in record['characterized_by']
