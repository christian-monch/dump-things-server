import json

import pytest  # noqa F401

from . import (
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
)
from .create_store import (
    given_name,
    identifier,
)

extra_record = {
    'id': 'abc:aaaa',
    'given_name': 'David',
}


def test_search_by_id(fastapi_client_simple):
    test_client, _ = fastapi_client_simple
    for i in range(1, 6):
        response = test_client.get(f'/collection_{i}/record?id={identifier}')
        assert json.loads(response.text) == {'id': identifier, 'given_name': given_name}


def test_store_record(fastapi_client_simple):
    test_client, _ = fastapi_client_simple
    for i in range(1, 6):
        response = test_client.post(
            f'/collection_{i}/record/Person',
            headers={'x-dumpthings-token': 'token_1'},
            json=extra_record,
        )
        assert response.status_code == HTTP_200_OK

    # Check that all stores can retrieve the record
    for i in range(1, 6):
        response = test_client.get(
            f'/collection_{i}/record?id={extra_record["id"]}',
            headers={'x-dumpthings-token': 'token_1'},
        )
        assert response.status_code == HTTP_200_OK
        assert json.loads(response.text) == extra_record

    # Check that all stores report two records, i.e. the default record
    # and the newly added record
    for i in range(1, 6):
        response = test_client.get(
            f'/collection_{i}/records/Person',
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

    # Check that subclasses are retrieved
    for i in range(1, 6):
        response = test_client.get(
            f'/collection_{i}/records/Thing',
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
            f'/collection_{i}/record/Person', json={'id': extra_record['id']}
        )
        assert response.status_code == HTTP_403_FORBIDDEN


def test_token_store_adding(fastapi_client_simple):
    test_client, store_dir = fastapi_client_simple
    response = test_client.post(
        '/collection_1/record/Person',
        headers={'x-dumpthings-token': 'david_bowie'},
        json={'id': extra_record['id']},
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED

    # Create token directory and retry
    (store_dir / 'token_stores' / 'david_bowie').mkdir()
    response = test_client.post(
        '/collection_1/record/Person',
        headers={'x-dumpthings-token': 'david_bowie'},
        json={'id': extra_record['id']},
    )
    assert response.status_code == HTTP_200_OK


def test_funky_id(fastapi_client_simple):
    test_client, _ = fastapi_client_simple
    record_id = 'trr379:contributors/someone'
    for i in range(1, 6):
        response = test_client.post(
            f'/collection_{i}/record/Person',
            headers={'x-dumpthings-token': 'token_1'},
            json={'id': record_id},
        )
        assert response.status_code == HTTP_200_OK

    # Try to find it
    for i in range(1, 6):
        response = test_client.get(
            f'/collection_{i}/record?id={record_id}',
            headers={'x-dumpthings-token': 'token_1'},
        )
        assert response.status_code == HTTP_200_OK


def test_token_store_priority(fastapi_client_simple):
    test_client, store_dir = fastapi_client_simple

    # Ensure a token directory existence
    (store_dir / 'token_stores' / 'david_bowie').mkdir(parents=True, exist_ok=True)

    # Post a record with the same id as the test record in the global store,
    # but use a different name.
    response = test_client.post(
        '/collection_1/record/Person',
        headers={'x-dumpthings-token': 'david_bowie'},
        json={'id': identifier, 'given_name': 'David'},
    )
    assert response.status_code == HTTP_200_OK

    # Check that the new record is returned with a token
    response = test_client.get(
        f'/collection_1/record?id={identifier}',
        headers={'x-dumpthings-token': 'david_bowie'},
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()['given_name'] == 'David'

    # Check that the global test record is returned without a token
    response = test_client.get(
        f'/collection_1/record?id={identifier}',
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()['given_name'] == 'Wolfgang'
