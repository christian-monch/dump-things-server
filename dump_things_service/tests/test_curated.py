from __future__ import annotations

from dump_things_service import (
    HTTP_200_OK,
)


def test_read_curated_records_of_class(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    for paginate in ('', 'p/'):
        response = test_client.get(
            f'/collection_1/curated/records/{paginate}Person',
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
                f'/collection_8/curated/records/{paginate}Person?matching={pattern}',
                headers={'x-dumpthings-token': 'token_1_xxxxx'},
            )
            assert response.status_code == HTTP_200_OK
            json_object = response.json()
            if 'items' in json_object:
                assert len(json_object['items']) == count
            else:
                assert len(json_object) == count
