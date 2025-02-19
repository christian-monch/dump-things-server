from collections import defaultdict

import yaml

from . import HTTP_200_OK

identifier = 'abc:this_is_an_identifier'

record_a = {
    'id': identifier,
    'given_name': 'James',
}

record_b = {
    'id': identifier,
    'given_name': 'Zulu',
}


def test_mapping_functions_ignore_data(fastapi_client_simple):
    test_client, store_path = fastapi_client_simple

    for i in range(1, 6):
        response = test_client.post(
            f'/collection_{i}/record/Person',
            headers={'x-dumpthings-token': 'token_1'},
            json=record_a,
        )
        assert response.status_code == HTTP_200_OK

        response = test_client.post(
            f'/collection_{i}/record/Person',
            headers={'x-dumpthings-token': 'token_1'},
            json=record_b,
        )
        assert response.status_code == HTTP_200_OK

        # Check that only one record with the given id exists in the collection
        id_counter = defaultdict(int)
        token_store_path = store_path / 'token_stores' / 'token_1' / f'collection_{i}'
        for path in token_store_path.rglob('*.yaml'):
            if path.is_file():
                record = yaml.load(path.read_text(), Loader=yaml.SafeLoader)
                id_counter[record['id']] += 1
        assert all(v == 1 for v in id_counter.values())
