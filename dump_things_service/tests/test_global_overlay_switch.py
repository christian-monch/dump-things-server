import pytest  # noqa F401

from . import HTTP_200_OK


def test_overlay(fastapi_client_simple):
    overlay_response, non_overlay_response = _get_responses(
        fastapi_client_simple[0],
    )

    assert len(overlay_response) >= len(non_overlay_response)
    assert len(non_overlay_response) == 0


def test_token_overlay(fastapi_client_simple):
    overlay_response, non_overlay_response = _get_responses(
        fastapi_client_simple[0],
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert len(overlay_response) >= len(non_overlay_response)


def _get_responses(test_client, *, headers=None):
    from dump_things_service.main import arguments

    overlay_response = test_client.get(
        '/collection_1/records/Thing',
        headers=headers,
    )
    assert overlay_response.status_code == HTTP_200_OK

    arguments.no_global_store = True
    non_overlay_response = test_client.get(
        '/collection_1/records/Thing',
        headers=headers,
    )
    assert non_overlay_response.status_code == HTTP_200_OK
    arguments.no_global_store = False

    return overlay_response.json(), non_overlay_response.json()
