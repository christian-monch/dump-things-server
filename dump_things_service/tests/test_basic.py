import json
from urllib.parse import quote

from .create_store import (
    identifier,
    dump_stores,
    fastapi_app,
    fastapi_client,
)


def test_search_by_id(fastapi_client):
    test_client, _ = fastapi_client
    for i in range(1, 6):
        response = test_client.get(f'/schema_{i}/record?id={quote(identifier)}')
        assert json.loads(response.text) == {'type': 'dltemporal:InstantaneousEvent', 'id': identifier}


def test_store_record(fastapi_client):
    test_client, _ = fastapi_client
    for i in range(1, 6):
        response = test_client.post(
            f'/schema_{i}/record/InstantaneousEvent',
            headers={'x-dumpthings-token': 'token_1'},
            json={'id': 'aaaa'}
        )
        assert response.status_code == 200

    for i in range(1, 6):
        response = test_client.get(f'/schema_{i}/record?id=aaaa')
        assert response.status_code == 200


def test_global_store_fails(fastapi_client):
    test_client, _ = fastapi_client
    for i in range(1, 6):
        response = test_client.post(
            f'/schema_{i}/record/InstantaneousEvent',
            json={'id': 'aaaa'}
        )
        assert response.status_code == 422


def test_token_store_adding(fastapi_client):
    test_client, store_dir = fastapi_client
    response = test_client.post(
        '/schema_1/record/InstantaneousEvent',
        headers={'x-dumpthings-token': 'david_bowie'},
        json={'id': 'aaaa'}
    )
    assert response.status_code == 401

    # Create token directory and retry
    (store_dir / 'token_stores' / 'david_bowie').mkdir()
    response = test_client.post(
        '/schema_1/record/InstantaneousEvent',
        headers={'x-dumpthings-token': 'david_bowie'},
        json={'id': 'aaaa'}
    )
    assert response.status_code == 200


def test_funky_id(fastapi_client):
    test_client, _ = fastapi_client
    record_id = 'trr379:contributors/stupid'
    for i in range(1, 6):
        response = test_client.post(
            f'/schema_{i}/record/InstantaneousEvent',
            headers={'x-dumpthings-token': 'token_1'},
            json={'id': record_id}
        )
        assert response.status_code == 200

    # Try to find it
    for i in range(1, 6):
        response = test_client.get(
            f'/schema_{i}/record?id={record_id}',
            headers={'x-dumpthings-token': 'token_1'},
        )
        assert response.status_code == 200
