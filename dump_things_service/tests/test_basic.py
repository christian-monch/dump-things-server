import json

import pytest  # F401

from .. import (
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
)
from ..utils import cleaned_json
from .create_store import (
    given_name,
    pid,
)
from .test_utils import basic_write_locations

extra_record = {
    'pid': 'abc:aaaa',
    'given_name': 'DavidÖÄÜ',
}

unicode_name = 'AlienÖÄÜ-ß👽'
unicode_bytes = unicode_name.encode('utf-8')
unicode_record = {
    'pid': 'abc:unicode-test',
    'given_name': unicode_name,
}


def test_search_by_pid(fastapi_client_simple):
    test_client, _ = fastapi_client_simple
    for i in range(1, 6):
        response = test_client.get(
            f'/collection_{i}/record?pid={pid}',
            headers={'x-dumpthings-token': 'basic_access'},
        )
        assert response.status_code == HTTP_200_OK
        assert json.loads(response.text) == {'pid': pid, 'given_name': given_name}


def test_search_by_pid_no_token(fastapi_client_simple):
    test_client, _ = fastapi_client_simple
    for i in range(1, 6):
        response = test_client.get(
            f'/collection_{i}/record?pid={pid}',
        )
        assert response.status_code == HTTP_200_OK
        assert response.json() == {'pid': pid, 'given_name': given_name}


def test_store_record(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Store a record in two collections
    for i, token in basic_write_locations:
        response = test_client.post(
            f'/collection_{i}/record/Person',
            headers={'x-dumpthings-token': token},
            json=extra_record,
        )
        assert response.status_code == HTTP_200_OK

    # Check that the existing record and the new records can be retrieved
    # from both collections
    for i, token in basic_write_locations:
        response = test_client.get(
            f'/collection_{i}/record?pid={extra_record["pid"]}',
            headers={'x-dumpthings-token': token},
        )
        assert response.status_code == HTTP_200_OK
        assert cleaned_json(
            response.json(),
            remove_keys=('annotations',)
        ) == extra_record

    # Check that other collections do not report the new record
    for i in range(3, 6):
        response = test_client.get(
            f'/collection_{i}/records/Person',
            headers={'x-dumpthings-token': 'basic_access'},
        )
        assert response.json() == [{'pid': pid, 'given_name': given_name}]

    # Check that subclasses are retrieved
    for i, token in basic_write_locations:
        response = test_client.get(
            f'/collection_{i}/records/Thing',
            headers={'x-dumpthings-token': token},
        )
        cleaned_response = cleaned_json(response.json(), remove_keys=('annotations',))
        assert extra_record in cleaned_response
        assert {'pid': pid, 'given_name': given_name} in cleaned_response


def test_encoding(fastapi_client_simple):
    test_client, store_path = fastapi_client_simple

    # Store a record with non-ASCII characters in collections via the API. that
    # will trigger the YAML-dumping, which should be checked
    response = test_client.post(
        '/collection_1/record/Person',
        headers={'x-dumpthings-token': 'token_1'},
        json=unicode_record,
    )
    assert response.status_code == HTTP_200_OK

    # Check that no '\\x'-encoding is present in files
    for item in store_path.glob('**/*.yaml'):
        encoded_content = item.read_bytes()
        assert b'\\x' not in encoded_content
        if b'Alien' in encoded_content:
            assert unicode_bytes in encoded_content


def test_global_store_write_fails(fastapi_client_simple):
    test_client, _ = fastapi_client_simple
    for i in range(1, 6):
        # Since we provide no token, the default token will be used. This will
        # only allow reading from curated, not posting.
        response = test_client.post(
            f'/collection_{i}/record/Person', json={'pid': extra_record['pid']}
        )
        assert response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.skip(reason='No runtime store adding yet')
def test_token_store_adding(fastapi_client_simple):
    test_client, store_dir = fastapi_client_simple
    response = test_client.post(
        '/collection_1/record/Person',
        headers={'x-dumpthings-token': 'david_bowie'},
        json={'pid': extra_record['pid']},
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED

    # Create collection-directory and token-directory and retry
    (store_dir / 'token_stores' / 'collection_1' / 'david_bowie').mkdir()
    response = test_client.post(
        '/collection_1/record/Person',
        headers={'x-dumpthings-token': 'david_bowie'},
        json={'pid': extra_record['pid']},
    )
    assert response.status_code == HTTP_200_OK


def test_funky_pid(fastapi_client_simple):
    test_client, _ = fastapi_client_simple
    record_pid = 'trr379:contributors/someone'
    for i, token in basic_write_locations:
        response = test_client.post(
            f'/collection_{i}/record/Person',
            headers={'x-dumpthings-token': token},
            json={'pid': record_pid},
        )
        assert response.status_code == HTTP_200_OK

    # Try to find it
    for i, token in basic_write_locations:
        response = test_client.get(
            f'/collection_{i}/record?pid={record_pid}',
            headers={'x-dumpthings-token': token},
        )
        assert response.status_code == HTTP_200_OK


def test_token_store_priority(fastapi_client_simple):
    test_client, store_dir = fastapi_client_simple

    # Post a record with the same pid as the global store's test record, but
    # with different content.
    response = test_client.post(
        '/collection_1/record/Person',
        headers={'x-dumpthings-token': 'token_1'},
        json={'pid': pid, 'given_name': 'DavidÖÄß'},
    )
    assert response.status_code == HTTP_200_OK

    # Check that the new record is returned with the token
    response = test_client.get(
        f'/collection_1/record?pid={pid}',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()['given_name'] == 'DavidÖÄß'

    # Check that the global test record is returned with basic access
    response = test_client.get(
        f'/collection_1/record?pid={pid}',
        headers={'x-dumpthings-token': 'basic_access'},
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()['given_name'] == given_name


def test_unknown_token(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Check that fetching with an unknown token is handled gracefully
    response = test_client.get(
        '/collection_1/record?pid=abc:unknown-token',
        headers={'x-dumpthings-token': 'unknown_token'},
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED

    # Check that posting with an unknown token is handled gracefully
    response = test_client.post(
        '/collection_1/record/Person',
        json={'pid': 'abc:unknown-token'},
        headers={'x-dumpthings-token': 'unknown_token'},
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED


def test_curie_expansion(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Check that the pid is expanded correctly
    response = test_client.get(
        '/collection_1/record?pid=http%3A%2F%2Fexample.org%2Fperson-schema%2Fabc%2Fmode_test',
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        'pid': 'abc:mode_test',
        'given_name': 'mode_curated',
    }
