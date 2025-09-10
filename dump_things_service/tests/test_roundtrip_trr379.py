import pytest  # noqa F401

from .. import HTTP_200_OK
from ..utils import cleaned_json

json_record = {
    'pid': 'trr379:test_john_json',
    'given_name': 'Johnöüß',
}
json_record_out = {
    'schema_type': 'dlflatsocial:Person',
    **json_record,
}

new_ttl_pid = 'dlflatsocial:another_john_json'

ttl_record = """@prefix dlflatsocial: <https://concepts.datalad.org/s/flat-social/unreleased/> .
@prefix dlsocialmx: <https://concepts.datalad.org/s/social-mixin/unreleased/> .
@prefix dlthings: <https://concepts.datalad.org/s/things/v1/> .

dlflatsocial:test_john_ttl a dlflatsocial:Person ;
    dlsocialmx:given_name "Johnöüß" ;
    dlthings:annotations [ a dlthings:Annotation ;
            dlthings:annotation_tag <http://purl.obolibrary.org/obo/NCIT_C54269> ;
            dlthings:annotation_value "test_user_1" ] .
"""

ttl_input_record = """@prefix dlflatsocial: <https://concepts.datalad.org/s/flat-social/unreleased/> .
@prefix dlsocialmx: <https://concepts.datalad.org/s/social-mixin/unreleased/> .
@prefix dlthings: <https://concepts.datalad.org/s/things/v1/> .

dlflatsocial:test_john_ttl a dlflatsocial:Person ;
    dlsocialmx:given_name "Johnöüß" .
"""

ttl_output_record = """@prefix dlflatsocial: <https://concepts.datalad.org/s/flat-social/unreleased/> .
@prefix dlsocialmx: <https://concepts.datalad.org/s/social-mixin/unreleased/> .
@prefix dlthings: <https://concepts.datalad.org/s/things/v1/> .
@prefix obo: <http://purl.obolibrary.org/obo/> .

dlflatsocial:test_john_ttl a dlflatsocial:Person ;
    dlsocialmx:given_name "Johnöüß" ;
    dlthings:annotations [ a dlthings:Annotation ;
            dlthings:annotation_tag obo:NCIT_C54269 ;
            dlthings:annotation_value "test_user_1" ] .
"""

new_json_pid = 'dlflatsocial:another_john_ttl'


def test_json_ttl_json_trr379(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    for i in range(1, 3):
        # Deposit JSON records
        response = test_client.post(
            f'/collection_trr379-{i}/record/Person',
            headers={'x-dumpthings-token': 'token_1'},
            json=json_record,
        )
        assert response.status_code == HTTP_200_OK

        # Retrieve TTL records
        response = test_client.get(
            f'/collection_trr379-{i}/record?pid={json_record["pid"]}&format=ttl',
            headers={'x-dumpthings-token': 'token_1'},
        )
        assert response.status_code == HTTP_200_OK
        ttl = response.text

        # modify the pid
        ttl = ttl.replace(json_record['pid'], new_ttl_pid)

        response = test_client.post(
            f'/collection_trr379-{i}/record/Person?format=ttl',
            headers={'content-type': 'text/turtle', 'x-dumpthings-token': 'token_1'},
            data=ttl,
        )
        assert response.status_code == HTTP_200_OK

        # Retrieve JSON record
        response = test_client.get(
            f'/collection_trr379-{i}/record?pid={new_ttl_pid}&format=json',
            headers={'x-dumpthings-token': 'token_1'},
        )
        assert response.status_code == HTTP_200_OK
        json_object = cleaned_json(response.json(), remove_keys=('annotations',))
        assert cleaned_json(json_object, remove_keys=('schema_type',)) != json_record
        json_object['pid'] = json_record['pid']
        assert json_object == json_record_out


#@pytest.mark.xfail
def test_ttl_json_ttl_trr379(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    for i in range(1, 3):
        # Deposit a ttl record
        response = test_client.post(
            f'/collection_trr379-{i}/record/Person?format=ttl',
            headers={
                'x-dumpthings-token': 'token_1',
                'content-type': 'text/turtle',
            },
            data=ttl_input_record,
        )
        assert response.status_code == HTTP_200_OK, 'Response content: ' + response.content.decode()

        # Retrieve JSON records
        response = test_client.get(
            f'/collection_trr379-{i}/record?pid=dlflatsocial:test_john_ttl&format=json',
            headers={'x-dumpthings-token': 'token_1'},
        )
        assert response.status_code == HTTP_200_OK
        json_object = response.json()

        # modify the pid
        json_object['pid'] = new_json_pid

        response = test_client.post(
            f'/collection_trr379-{i}/record/Person?format=json',
            headers={'x-dumpthings-token': 'token_1'},
            json=json_object,
        )
        assert response.status_code == HTTP_200_OK

        # Retrieve ttl record
        response = test_client.get(
            f'/collection_trr379-{i}/record?pid={new_json_pid}&format=ttl',
            headers={'x-dumpthings-token': 'token_1'},
        )
        assert response.status_code == HTTP_200_OK
        assert (
            response.text.strip()
            == ttl_output_record.replace('dlflatsocial:test_john_ttl', new_json_pid).strip()
        )
