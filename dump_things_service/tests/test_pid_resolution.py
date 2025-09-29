

from .. import HTTP_400_BAD_REQUEST


def test_store_record_with_unresolvable_pid(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Store a record in two collections
    response = test_client.post(
        f'/collection_1/record/Person',
        headers={'x-dumpthings-token': 'token-1'},
        json={'pid': 'unknown_prefix:test_pid'},
    )
    assert response.status_code == HTTP_400_BAD_REQUEST



def test_store_record_curated_with_unresolvable_pid(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Store a record in two collections
    response = test_client.post(
        f'/collection_1/curated/record/Person',
        headers={'x-dumpthings-token': 'token_admin'},
        json={'pid': 'unknown_prefix:test_pid'},
    )
    assert response.status_code == HTTP_400_BAD_REQUEST


def test_store_record_incoming_with_unresolvable_pid(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Store a record in two collections
    response = test_client.post(
        f'/collection_1/incoming/in_token_1/record/Person',
        headers={'x-dumpthings-token': 'token_admin'},
        json={'pid': 'unknown_prefix:test_pid'},
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
