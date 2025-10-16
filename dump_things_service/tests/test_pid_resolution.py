import pytest

from .. import HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize('pid', ['unknown_prefix:test_pid', 'abc:test_öö_pid'])
@pytest.mark.parametrize('url_part', ['', 'curated/', 'incoming/in_token_1/'])
def test_store_record_validation(fastapi_client_simple, pid, url_part):
    test_client, _ = fastapi_client_simple

    # Store a record in two collections
    response = test_client.post(
        f'/collection_1/{url_part}record/Person',
        headers={'x-dumpthings-token': 'token-1'},
        json={'pid': pid},
    )
    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT


x = """
def test_store_record_curated_with_unresolvable_pid(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Store a record in two collections
    response = test_client.post(
        f'/collection_1/curated/record/Person',
        headers={'x-dumpthings-token': 'token_admin'},
        json={'pid': 'unknown_prefix:test_pid'},
    )
    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT


def test_store_record_incoming_with_unresolvable_pid(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Store a record in two collections
    response = test_client.post(
        f'/collection_1/incoming/in_token_1/record/Person',
        headers={'x-dumpthings-token': 'token_admin'},
        json={'pid': 'unknown_prefix:test_pid'},
    )
    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT


def test_store_record_with_non_ascii_pid(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Store a record in two collections
    response = test_client.post(
        f'/collection_1/record/Person',
        headers={'x-dumpthings-token': 'token-1'},
        json={'pid': 'abc:test_pid'},
    )
    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT
"""
