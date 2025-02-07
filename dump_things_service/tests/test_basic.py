import json

from .create_store import (
    identifier,
    dump_stores_simple,
    fastapi_app_simple,
    fastapi_client_simple,
    given_name,
)

extra_record = {'id': 'ex:aaaa', 'given_name': 'David'}


def test_search_by_id(fastapi_client_simple):
    test_client, _ = fastapi_client_simple
    for i in range(1, 6):
        response = test_client.get(f'/store_{i}/record?id={identifier}')
        assert json.loads(response.text) == {'id': identifier, 'given_name': given_name}


def test_store_record(fastapi_client_simple):
    test_client, _ = fastapi_client_simple
    for i in range(1, 6):
        response = test_client.post(
            f'/store_{i}/record/Person',
            headers={'x-dumpthings-token': 'token_1'},
            json=extra_record
        )
        assert response.status_code == 200

    # Check that all stores can retrieve the record
    for i in range(1, 6):
        response = test_client.get(
            f'/store_{i}/record?id={extra_record["id"]}',
            headers={'x-dumpthings-token': 'token_1'},
        )
        assert response.status_code == 200
        assert json.loads(response.text) == extra_record

    # Check that all stores report two records, i.e. the default record
    # and the newly added record
    for i in range(1, 6):
        response = test_client.get(
            f'/store_{i}/records/Person',
            headers={'x-dumpthings-token': 'token_1'},
       )
        assert sorted(
            json.loads(response.text),
            key=lambda x: x['id'],
        ) == sorted(
            [
                {'id': identifier, 'given_name': given_name},
                extra_record,
            ],
            key=lambda x: x['id'],
        )


def test_global_store_fails(fastapi_client_simple):
    test_client, _ = fastapi_client_simple
    for i in range(1, 6):
        response = test_client.post(
            f'/store_{i}/record/Person',
            json={'id': extra_record['id']}
        )
        assert response.status_code == 422


def test_token_store_adding(fastapi_client_simple):
    test_client, store_dir = fastapi_client_simple
    response = test_client.post(
        '/store_1/record/Person',
        headers={'x-dumpthings-token': 'david_bowie'},
        json={'id': extra_record['id']}
    )
    assert response.status_code == 401

    # Create token directory and retry
    (store_dir / 'token_stores' / 'david_bowie').mkdir()
    response = test_client.post(
        '/store_1/record/Person',
        headers={'x-dumpthings-token': 'david_bowie'},
        json={'id': extra_record['id']}
    )
    assert response.status_code == 200


def test_funky_id(fastapi_client_simple):
    test_client, _ = fastapi_client_simple
    record_id = 'trr379:contributors/someone'
    for i in range(1, 6):
        response = test_client.post(
            f'/store_{i}/record/Person',
            headers={'x-dumpthings-token': 'token_1'},
            json={'id': record_id}
        )
        assert response.status_code == 200

    # Try to find it
    for i in range(1, 6):
        response = test_client.get(
            f'/store_{i}/record?id={record_id}',
            headers={'x-dumpthings-token': 'token_1'},
        )
        assert response.status_code == 200
