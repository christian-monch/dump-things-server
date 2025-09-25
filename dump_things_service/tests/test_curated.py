from __future__ import annotations

import pytest

from dump_things_service import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
)


@pytest.mark.parametrize('paginate', ('', 'p/'))
@pytest.mark.parametrize('class_name', ('', 'Person'))
def test_read_curated_records(
    fastapi_client_simple,
    paginate,
    class_name,
):
    test_client, _ = fastapi_client_simple

    response = test_client.get(
        f'/collection_1/curated/records/{paginate}{class_name}',
        headers={'x-dumpthings-token': 'token_1_xxxxx'},
    )
    assert response.status_code == HTTP_200_OK
    json_object = response.json()

    if 'items' in json_object:
        assert len(json_object['items']) == 3
    else:
        assert len(json_object) == 3

    for pattern, count in (('%25wolf%25', 1), ('%25cura%25', 2)):
        test_client, _ = fastapi_client_simple
        response = test_client.get(
            f'/collection_8/curated/records/{paginate}{class_name}?matching={pattern}',
            headers={'x-dumpthings-token': 'token_1_xxxxx'},
        )
        assert response.status_code == HTTP_200_OK
        json_object = response.json()
        if 'items' in json_object:
            assert len(json_object['items']) == count
        else:
            assert len(json_object) == count


pytest.mark.parametrize(
    'pid',
    ('abc:mode_test', 'abc:some_timee@x.com', 'abc:curated'),
)
def test_read_curated_records_by_pid(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    response = test_client.get(
        f'/no_such_collection/curated/records/',
        headers={'x-dumpthings-token': 'token_1_xxxxx'},
    )
    assert response.status_code == HTTP_404_NOT_FOUND


def test_unknown_collection(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    response = test_client.get(
        f'/no_such_collection/curated/records/',
        headers={'x-dumpthings-token': 'token_1_xxxxx'},
    )
    assert response.status_code == HTTP_404_NOT_FOUND
