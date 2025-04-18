import pytest  # noqa F401

from . import HTTP_200_OK


json_record = {'pid': 'xyz:bbbb', 'given_name': 'John'}
new_ttl_pid = 'xyz:cccc'

ttl_record = """@prefix abc: <http://example.org/person-schema/abc/> .
@prefix xyz: <http://example.org/person-schema/xyz/> .

xyz:HenryAdams a abc:Person ;
    abc:given_name "Henry" .
"""
new_json_pid = 'xyz:HenryBaites'


def test_json_ttl_json(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Deposit JSON records
    response = test_client.post(
        '/collection_1/record/Person',
        headers={'x-dumpthings-token': 'token_1'},
        json=json_record,
    )
    assert response.status_code == HTTP_200_OK

    # Retrieve TTL records
    response = test_client.get(
        f'/collection_1/record?pid={json_record["pid"]}&format=ttl',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == HTTP_200_OK
    ttl = response.text

    # modify the pid
    ttl = ttl.replace(json_record['pid'], new_ttl_pid)

    response = test_client.post(
        '/collection_1/record/Person?format=ttl',
        headers={'content-type': 'text/turtle', 'x-dumpthings-token': 'token_1'},
        data=ttl,
    )
    assert response.status_code == HTTP_200_OK

    # Retrieve JSON record
    response = test_client.get(
        f'/collection_1/record?pid={new_ttl_pid}&format=json',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == HTTP_200_OK
    json_object = response.json()
    assert json_object != json_record
    json_object['pid'] = json_record['pid']
    assert json_object == json_record


def test_ttl_json_ttl(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Deposit a ttl record
    response = test_client.post(
        '/collection_1/record/Person?format=ttl',
        headers={
            'x-dumpthings-token': 'token_1',
            'content-type': 'text/turtle',
        },
        data=ttl_record,
    )
    assert response.status_code == HTTP_200_OK

    # Retrieve JSON records
    response = test_client.get(
        '/collection_1/record?pid=xyz:HenryAdams&format=json',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == HTTP_200_OK
    json_object = response.json()

    # modify the pid
    json_object['pid'] = new_json_pid

    response = test_client.post(
        '/collection_1/record/Person?format=json',
        headers={'x-dumpthings-token': 'token_1'},
        json=json_object,
    )
    assert response.status_code == HTTP_200_OK

    # Retrieve ttl record
    response = test_client.get(
        f'/collection_1/record?pid={new_json_pid}&format=ttl',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == HTTP_200_OK
    assert (
        response.text.strip()
        == ttl_record.replace('xyz:HenryAdams', new_json_pid).strip()
    )
