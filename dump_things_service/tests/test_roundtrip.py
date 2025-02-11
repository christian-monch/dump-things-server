import pytest


json_record = {'id': 'xyz:bbbb', 'given_name': 'John'}
new_ttl_id = 'xyz:cccc'

ttl_record = """@prefix abc: <http://example.org/person-schema/abc/> .
@prefix xyz: <http://example.org/person-schema/xyz/> .

xyz:HenryAdams a abc:Person ;
    abc:given_name "Henry" .
"""
new_json_id = 'xyz:HenryBaites'


def test_json_ttl_json(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Deposit JSON records
    response = test_client.post(
        f'/store_1/record/Person',
        headers={'x-dumpthings-token': 'token_1'},
        json=json_record
    )
    assert response.status_code == 200

    # Retrieve TTL records
    response = test_client.get(
        f'/store_1/record?id={json_record["id"]}&format=ttl',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == 200
    ttl = response.text

    # modify the id
    ttl = ttl.replace(json_record['id'], new_ttl_id)

    response = test_client.post(
        f'/store_1/record/Person?format=ttl',
        headers={
            'content-type': 'text/turtle',
            'x-dumpthings-token': 'token_1'
        },
        data=ttl
    )
    assert response.status_code == 200

    # Retrieve JSON record
    response = test_client.get(
        f'/store_1/record?id={new_ttl_id}&format=json',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == 200
    json_object = response.json()
    assert json_object != json_record
    json_object['id'] = json_record['id']
    assert json_object == json_record


def test_ttl_json_ttl(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Deposit a ttl record
    response = test_client.post(
        f'/store_1/record/Person?format=ttl',
        headers={
            'x-dumpthings-token': 'token_1',
            'content-type': 'text/turtle',
        },
        data=ttl_record
    )
    assert response.status_code == 200

    # Retrieve JSON records
    response = test_client.get(
        f'/store_1/record?id=xyz:HenryAdams&format=json',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == 200
    json_object = response.json()

    # modify the id
    json_object['id'] = new_json_id

    response = test_client.post(
        f'/store_1/record/Person?format=json',
        headers={
            'x-dumpthings-token': 'token_1'
        },
        json=json_object
    )
    assert response.status_code == 200

    # Retrieve ttl record
    response = test_client.get(
        f'/store_1/record?id={new_json_id}&format=ttl',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == 200
    assert response.text.strip() == ttl_record.replace(
        'xyz:HenryAdams', new_json_id
    ).strip()
