import pytest  # noqa F401

from . import (
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED,
)
from .create_store import pid

extra_record = {
    'pid': 'abc:bbbbb',
    'given_name': 'Josephine',
}


def test_read_access(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Ensure that token-less access is always allowed
    response = test_client.get(f'/collection_1/record?pid={pid}')
    assert response.status_code == HTTP_200_OK

    # Ensure that read access is controlled by `read_access`, independent of
    # `write_access`.
    response = test_client.get(
        f'/collection_1/record?pid={pid}',
        headers={'x-dumpthings-token': 'token_1_oo'}
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    response = test_client.get(
        f'/collection_1/record?pid={pid}',
        headers={'x-dumpthings-token': 'token_1_ox'}
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED


def test_write_access(fastapi_client_simple):
    test_client, _ = fastapi_client_simple
    json_record = {'pid': 'xyz:jjjj', 'given_name': 'Josephine'}

    # Ensure that write access is controlled by `write_access` independent
    # of `read_access`.
    response = test_client.post(
        '/collection_1/record/Person',
        headers={'x-dumpthings-token': 'token_1_ox'},
        json=json_record,
    )
    assert response.status_code == HTTP_200_OK
    response = test_client.post(
        '/collection_1/record/Person',
        headers={'x-dumpthings-token': 'token_1_xx'},
        json=json_record,
    )
    assert response.status_code == HTTP_200_OK
    response = test_client.post(
        '/collection_1/record/Person',
        headers={'x-dumpthings-token': 'token_1_xo'},
        json=json_record,
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
