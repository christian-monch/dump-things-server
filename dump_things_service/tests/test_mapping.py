from collections import defaultdict

import yaml

from . import HTTP_200_OK

pid = 'abc:this_is_a_persistent_identifier'

record_a = {
    'pid': pid,
    'given_name': 'James',
}

record_b = {
    'pid': pid,
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

        # Check that only one record with the given pid exists in the collection
        pid_counter = defaultdict(int)
        token_store_path = store_path / 'token_stores' / 'token_1' / f'collection_{i}'
        for path in token_store_path.rglob('*.yaml'):
            if path.is_file():
                record = yaml.load(path.read_text(), Loader=yaml.SafeLoader)
                pid_counter[record['pid']] += 1
        assert all(v == 1 for v in pid_counter.values())
