from __future__ import annotations

from .. import (
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED,
)


def verify_permission_fetching(
    test_client,
    token: str,
    expected_status: tuple[int, tuple[bool, bool, bool]],
):
    response = test_client.post(
        '/collection_1/token_permissions',
        json={'token': token},
    )
    http_status, (read_curated, read_incoming, write_incoming) = expected_status
    assert response.status_code == http_status
    if http_status == HTTP_200_OK:
        result = response.json()
        assert result['read_curated'] == read_curated
        assert result['read_incoming'] == read_incoming
        assert result['write_incoming'] == write_incoming
        if read_incoming or write_incoming:
            assert result['incoming_zone'] == 'modes'
        else:
            assert 'incoming_zone' not in result


def test_permission_fetching(fastapi_client_simple):
    test_client, store_dir = fastapi_client_simple

    verify_permission_fetching(
        test_client=test_client,
        token='this-is-not-a-token',  # noqa S106
        expected_status=(HTTP_401_UNAUTHORIZED, (False, False, False)),
    )

    for permissions in [
        # READ_COLLECTION
        (True, True, False),
        # WRITE_COLLECTION
        (True, True, True),
        # READ_SUBMISSION
        (False, True, False),
        # WRITE_SUBMISSIONS
        (False, True, True),
        # SUBMIT
        (True, False, True),
        # SUBMIT_ONLY
        (False, False, True),
        # READ_CURATED
        (True, False, False),
        # NOTHING
        (False, False, False),
    ]:
        token = 'token_1_' + ''.join('x' if x else 'o' for x in permissions)
        verify_permission_fetching(
            test_client=test_client,
            token=token,
            expected_status=(HTTP_200_OK, permissions),
        )
