import pytest  # noqa F401

from . import HTTP_200_OK

json_record = {
    'id': 'trr379:test_john_json',
    'schema_type': 'dlsocial:Person',
    'given_name': 'John',
}

new_ttl_id = 'trr379:another_john_json'


ttl_record = """
@prefix dlsocial: <https://concepts.datalad.org/s/social/unreleased/> .
@prefix trr379: <https://trr379.de/> .

trr379:test_john_ttl a dlsocial:Person ;
    dlsocial:given_name "John" .
"""

new_json_id = 'trr379:another_john_ttl'


def test_json_ttl_json_trr379(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Deposit JSON records
    response = test_client.post(
        '/collection_trr379/record/Person',
        headers={'x-dumpthings-token': 'token_1'},
        json=json_record,
    )
    assert response.status_code == HTTP_200_OK

    # Retrieve TTL records
    response = test_client.get(
        f'/collection_trr379/record?id={json_record["id"]}&format=ttl',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == HTTP_200_OK
    ttl = response.text

    # modify the id
    ttl = ttl.replace(json_record['id'], new_ttl_id)

    response = test_client.post(
        '/collection_trr379/record/Person?format=ttl',
        headers={'content-type': 'text/turtle', 'x-dumpthings-token': 'token_1'},
        data=ttl,
    )
    assert response.status_code == HTTP_200_OK

    # Retrieve JSON record
    response = test_client.get(
        f'/collection_trr379/record?id={new_ttl_id}&format=json',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == HTTP_200_OK
    json_object = response.json()
    assert json_object != json_record
    json_object['id'] = json_record['id']
    assert json_object == json_record


def test_ttl_json_ttl_trr379(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Deposit a ttl record
    response = test_client.post(
        '/collection_trr379/record/Person?format=ttl',
        headers={
            'x-dumpthings-token': 'token_1',
            'content-type': 'text/turtle',
        },
        data=ttl_record,
    )
    assert response.status_code == HTTP_200_OK

    # Retrieve JSON records
    response = test_client.get(
        '/collection_trr379/record?id=trr379:test_john_ttl&format=json',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == HTTP_200_OK
    json_object = response.json()

    # modify the id
    json_object['id'] = new_json_id

    response = test_client.post(
        '/collection_trr379/record/Person?format=json',
        headers={'x-dumpthings-token': 'token_1'},
        json=json_object,
    )
    assert response.status_code == HTTP_200_OK

    # Retrieve ttl record
    response = test_client.get(
        f'/collection_trr379/record?id={new_json_id}&format=ttl',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == HTTP_200_OK
    assert (
        response.text.strip()
        == ttl_record.replace('trr379:test_john_ttl', new_json_id).strip()
    )
