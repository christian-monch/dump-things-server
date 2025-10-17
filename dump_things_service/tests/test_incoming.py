from __future__ import annotations

import pytest
import random

from dump_things_service import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
)
from dump_things_service.tests.test_auth import repo_1

delete_record = {
    'schema_type': 'abc:Person',
    'pid': 'abc:delete-me',
    'given_name': 'Detlef',
}


def test_incoming_labels(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    for i in range(1, 9):
        response = test_client.get(
            f'/collection_{i}/incoming/',
            headers={'x-dumpthings-token': 'token_admin'},
        )
        existing_labels = response.json()
        assert len(existing_labels) >= 1


zones_filled = False

def fill_zones(test_client):
    global zones_filled

    if zones_filled:
        return

    for collection_id, label in (
        (1, 'admin_1'),
        (2, 'admin_2'),
        (3, 'admin_3'),
        (4, 'admin_4'),
        (5, 'admin_common'),
        (6, 'admin_common'),
        (7, 'admin_common'),
        (8, 'admin_common'),
    ):
        token = 'token_admin'
        result = test_client.post(
            f'/collection_{collection_id}/incoming/{label}/record/Person',
            headers={'x-dumpthings-token': token},
            json={
                'pid': f'abc:test_incoming-collection_{collection_id}-{token}',
                'given_name': f'collection_{collection_id}-{token}',
            }
        )
        assert result.status_code == HTTP_200_OK

    zones_filled = True


@pytest.mark.parametrize('paginate', ('', 'p/'))
@pytest.mark.parametrize('class_name', ('', 'Person'))
def test_read_incoming_records(
    fastapi_client_simple,
    paginate: str,
    class_name: str,
):
    test_client, _ = fastapi_client_simple

    fill_zones(test_client)

    for collection_id, labels in (
            (1, ['modes', 'admin_1', 'cmo', 'in_token_1']),
            (2, ['in_token-2', 'admin_2']),
            (3, ['admin_3']),
            (4, ['admin_4']),
            (5, ['admin_common']),
            (6, ['admin_common']),
            (7, ['admin_common']),
            (8, ['modes', 'test_user_8', 'admin_common']),
    ):
        # Check that all incoming zones are reached
        for label in labels:
            response = test_client.get(
                f'/collection_{collection_id}/incoming/{label}/records/{paginate}{class_name}',
                headers={'x-dumpthings-token': 'token_admin'},
            )
            assert response.status_code == HTTP_200_OK
            # We don't know the exact number of entries in each zone, because
            # it depends on the tests that ran before.

        # Check for deposited records
        for label in labels:
            expected_length = 0
            if label.startswith('admin_'):
                expected_length = 1
            pattern = f'abc:test_incoming-collection_{collection_id}-token_admin'
            response = test_client.get(
                f'/collection_{collection_id}/incoming/{label}/records/{paginate}{class_name}?matching={pattern}',
                headers={'x-dumpthings-token': 'token_admin'},
            )
            assert response.status_code == HTTP_200_OK
            json_object = response.json()
            if 'items' in json_object:
                result = json_object['items']
            else:
                result = json_object
            matching = [
                json_object
                for json_object in result
                if json_object['pid'] == pattern
            ]
            assert len(matching) == expected_length, f'did not find {expected_length} record: collection_{collection_id}, {label}, {result}'


pytest.mark.parametrize(
    'pid',
    ('abc:mode_test', 'abc:some_timee@x.com', 'abc:curated'),
)
def test_read_incoming_records_by_pid(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    response = test_client.get(
        '/no_such_collection/curated/records/',
        headers={'x-dumpthings-token': 'token_1_xxxxx'},
    )
    assert response.status_code == HTTP_404_NOT_FOUND


def test_incoming_unknown_collection(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    response = test_client.get(
        '/no_such_collection/incoming/no_such_label/records/',
        headers={'x-dumpthings-token': 'token_admin'},
    )
    assert response.status_code == HTTP_404_NOT_FOUND


def test_incoming_unknown_label(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    response = test_client.get(
        '/collection_1/incoming/no_such_label/records/',
        headers={'x-dumpthings-token': 'token_admin'},
    )
    assert response.status_code == HTTP_404_NOT_FOUND


def test_incoming_delete(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    response = test_client.post(
        '/collection_7/incoming/admin_common/record/Person',
        headers={'x-dumpthings-token': 'token_admin'},
        json=delete_record,
    )
    assert response.status_code == HTTP_200_OK

    response = test_client.get(
        '/collection_7/incoming/admin_common/record?pid=abc:delete-me',
        headers={'x-dumpthings-token': 'token_admin'},
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()['json_object']['pid'] == 'abc:delete-me'

    response = test_client.delete(
        '/collection_7/incoming/admin_common/record?pid=abc:delete-me',
        headers={'x-dumpthings-token': 'token_admin'},
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() is True

    response = test_client.get(
        '/collection_7/incoming/admin_common/record?pid=abc:delete-me',
        headers={'x-dumpthings-token': 'token_admin'},
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() is None

    response = test_client.delete(
        '/collection_7/incoming/admin_common/record?pid=abc:delete-me',
        headers={'x-dumpthings-token': 'token_admin'},
    )
    assert response.status_code == HTTP_404_NOT_FOUND


def test_incoming_on_disk_only(fastapi_client_simple):
    test_client, data_root = fastapi_client_simple

    # add a random directory to the incoming area of collection_1
    random_part = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=6))
    dir_name = f'random_{random_part}'
    (data_root / 'incoming' / dir_name).mkdir()

    response = test_client.get(
        '/collection_1/incoming/',
        headers={'x-dumpthings-token': 'token_admin'},
    )
    assert response.status_code == HTTP_200_OK
    assert dir_name in response.json()
