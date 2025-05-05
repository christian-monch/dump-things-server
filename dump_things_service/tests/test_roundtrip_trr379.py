import pytest  # noqa F401

from .. import HTTP_200_OK

json_record = {
    'pid': 'trr379:test_john_json',
    'schema_type': 'dlsocial:Person',
    'given_name': 'Johnöüß',
}

new_ttl_pid = 'trr379:another_john_json'


ttl_record = """
@prefix dlsocial: <https://concepts.datalad.org/s/social/unreleased/> .
@prefix trr379: <https://trr379.de/> .

trr379:test_john_ttl a dlsocial:Person ;
    dlsocial:given_name "Johnöüß" .
"""

new_json_pid = 'trr379:another_john_ttl'


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
        f'/collection_trr379/record?pid={json_record["pid"]}&format=ttl',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == HTTP_200_OK
    ttl = response.text

    # modify the pid
    ttl = ttl.replace(json_record['pid'], new_ttl_pid)

    response = test_client.post(
        '/collection_trr379/record/Person?format=ttl',
        headers={'content-type': 'text/turtle', 'x-dumpthings-token': 'token_1'},
        data=ttl,
    )
    assert response.status_code == HTTP_200_OK

    # Retrieve JSON record
    response = test_client.get(
        f'/collection_trr379/record?pid={new_ttl_pid}&format=json',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == HTTP_200_OK
    json_object = response.json()
    assert json_object != json_record
    json_object['pid'] = json_record['pid']
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
        '/collection_trr379/record?pid=trr379:test_john_ttl&format=json',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == HTTP_200_OK
    json_object = response.json()

    # modify the pid
    json_object['pid'] = new_json_pid

    response = test_client.post(
        '/collection_trr379/record/Person?format=json',
        headers={'x-dumpthings-token': 'token_1'},
        json=json_object,
    )
    assert response.status_code == HTTP_200_OK

    # Retrieve ttl record
    response = test_client.get(
        f'/collection_trr379/record?pid={new_json_pid}&format=ttl',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == HTTP_200_OK
    assert (
        response.text.strip()
        == ttl_record.replace('trr379:test_john_ttl', new_json_pid).strip()
    )
