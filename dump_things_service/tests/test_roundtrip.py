import json

from .create_store import (
    identifier,
    dump_stores_simple,
    fastapi_app_simple,
    fastapi_client_simple,
    given_name,
)


extra_record = {'id': 'ex:bbbb', 'given_name': 'John'}
new_id = 'ex:cccc'


def test_json_to_json(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Deposit JSON records
    response = test_client.post(
        f'/store_1/record/Person',
        headers={'x-dumpthings-token': 'token_1'},
        json=extra_record
    )

    # Retrieve TTL records
    response = test_client.get(
        f'/store_1/record?id={extra_record["id"]}&format=ttl',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == 200
    ttl = response.text

    # modify the id
    ttl = ttl.replace(extra_record['id'], new_id)

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
        f'/store_1/record?id={new_id}&format=json',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == 200
    json_object = response.json()
    assert json_object != extra_record
    json_object['id'] = extra_record['id']
    assert json_object == extra_record
