from __future__ import annotations

from typing import TYPE_CHECKING

from .. import (
    HTTP_200_OK,
    HTTP_403_FORBIDDEN,
)

if TYPE_CHECKING:
    from collections.abc import Iterable


def verify_modes(
    test_client,
    write_expactations: Iterable[tuple[str, str, int]],
    read_class_expectations: Iterable[tuple[str, str, int, tuple[int, int]]],
    read_pid_expectations: Iterable[tuple[str, str, int, str]],
):
    for collection, token, expected_status in write_expactations:
        response = test_client.post(
            f'/{collection}/record/Person',
            headers={'x-dumpthings-token': token},
            json={'pid': 'abc:incoming', 'given_name': 'incoming'},
        )
        assert response.status_code == expected_status

    for collection, token, expected_status, (
        curated_count,
        incoming_count,
    ) in read_class_expectations:
        response = test_client.get(
            f'/{collection}/records/Person',
            headers={'x-dumpthings-token': token},
        )
        assert response.status_code == expected_status
        if response.status_code == HTTP_200_OK:
            names = [x['given_name'] for x in response.json()]
            assert names.count('curated') == curated_count
            assert names.count('incoming') == incoming_count

    for collection, token, expected_status, expected_name in read_pid_expectations:
        response = test_client.get(
            f'/{collection}/record?pid=abc:mode_test',
            headers={'x-dumpthings-token': token},
        )
        assert response.status_code == expected_status
        if response.status_code == HTTP_200_OK:
            assert response.json()['given_name'] == expected_name


def test_token_modes(fastapi_client_simple):
    test_client, store_dir = fastapi_client_simple

    # Post a record to incoming of collections `collection_1`. We use it to
    # validate read/write permissions on class-base
    response = test_client.post(
        '/collection_1/record/Person',
        headers={'x-dumpthings-token': 'token_1'},
        json={'pid': 'abc:incoming', 'given_name': 'incoming'},
    )
    assert response.status_code == HTTP_200_OK

    # Post a record to incoming of collections `collection_1`. We use it to
    # validate read/write permissions id-based access. A record with the same
    # id, i.e. `abc:mode_test` exists in the default curated test store.
    response = test_client.post(
        '/collection_1/record/Person',
        headers={'x-dumpthings-token': 'token_1_xxx'},
        json={'pid': 'abc:mode_test', 'given_name': 'mode_incoming'},
    )

    # The modes we check are described below. Flags (o: False, x: True) indicate
    # which read, write permissions are given. They are in the order:
    #
    #   read curated, read staging, write staging.
    #
    # The test store contains `token_1_{flag}' for collection `collection_1`
    # the following flags:
    #
    # flag: xxo  READ_COLLECTION (read staging, read curated)
    # flag: xxx  WRITE_COLLECTION (read staging, read curated, write staging)
    # flag: oxo  READ_SUBMISSIONS (read staging)
    # flag: oxx  WRITE_SUBMISSIONS (read staging, write staging)
    # flag: xox  SUBMIT (read_curated, write staging)
    # flag: oox  SUBMIT_ONLY (write staging)
    # flag: xoo  READ_CURATED (read_curated)
    # flag: ooo  NOTHING ()

    # Because the default token permits read access to curated, all tokens
    # will at least have this access.
    verify_modes(
        test_client=test_client,
        write_expactations=[
            # READ_COLLECTION | READ_CURATED
            ('collection_1', 'token_1_xxo', HTTP_403_FORBIDDEN),
            # WRITE_COLLECTION | READ_CURATED
            ('collection_1', 'token_1_xxx', HTTP_200_OK),
            # READ_SUBMISSION | READ_CURATED
            ('collection_1', 'token_1_oxo', HTTP_403_FORBIDDEN),
            # WRITE_SUBMISSIONS | READ_CURATED
            ('collection_1', 'token_1_oxx', HTTP_200_OK),
            # SUBMIT | READ_CURATED
            ('collection_1', 'token_1_xox', HTTP_200_OK),
            # SUBMIT_ONLY | READ_CURATED
            ('collection_1', 'token_1_oox', HTTP_200_OK),
            # READ_CURATED | READ_CURATED
            ('collection_1', 'token_1_xoo', HTTP_403_FORBIDDEN),
            # NOTHING | READ_CURATED
            ('collection_1', 'token_1_ooo', HTTP_403_FORBIDDEN),
        ],
        read_class_expectations=[
            # READ_COLLECTION | READ_CURATED
            ('collection_1', 'token_1_xxo', HTTP_200_OK, (1, 1)),
            # WRITE_COLLECTION | READ_CURATED
            ('collection_1', 'token_1_xxx', HTTP_200_OK, (1, 1)),
            # READ_SUBMISSIONS | READ_CURATED
            ('collection_1', 'token_1_oxo', HTTP_200_OK, (1, 1)),
            # WRITE_SUBMISSIONS | READ_CURATED
            ('collection_1', 'token_1_oxx', HTTP_200_OK, (1, 1)),
            # SUBMIT | READ_CURATED
            ('collection_1', 'token_1_xox', HTTP_200_OK, (1, 0)),
            # SUBMIT_ONLY | READ_CURATED
            ('collection_1', 'token_1_oox', HTTP_200_OK, (1, 0)),
            # READ_CURATED | READ_CURATED
            ('collection_1', 'token_1_xoo', HTTP_200_OK, (1, 0)),
            # NOTHING | READ_CURATED
            ('collection_1', 'token_1_ooo', HTTP_200_OK, (1, 0)),
        ],
        read_pid_expectations=[
            # READ_COLLECTION | READ_CURATED
            ('collection_1', 'token_1_xxo', HTTP_200_OK, 'mode_incoming'),
            # WRITE_COLLECTION | READ_CURATED
            ('collection_1', 'token_1_xxx', HTTP_200_OK, 'mode_incoming'),
            # READ_SUBMISSIONS | READ_CURATED
            ('collection_1', 'token_1_oxo', HTTP_200_OK, 'mode_incoming'),
            # WRITE_SUBMISSIONS | READ_CURATED
            ('collection_1', 'token_1_oxx', HTTP_200_OK, 'mode_incoming'),
            # SUBMIT | READ_CURATED
            ('collection_1', 'token_1_xox', HTTP_200_OK, 'mode_curated'),
            # SUBMIT_ONLY | READ_CURATED
            ('collection_1', 'token_1_oox', HTTP_200_OK, 'mode_curated'),
            # READ_CURATED | READ_CURATED
            ('collection_1', 'token_1_xoo', HTTP_200_OK, 'mode_curated'),
            # NOTHING | READ_CURATED
            ('collection_1', 'token_1_ooo', HTTP_200_OK, 'mode_curated'),
        ],
    )
