import pytest  # noqa F401

from .. import HTTP_200_OK
from ..utils import cleaned_json

json_record = {
    'pid': 'trr379:test_john_json',
    'given_name': 'Johnöüß',
}

new_ttl_pid = 'trr379:another_john_json'

ttl_record = """@prefix dlsocial: <https://concepts.datalad.org/s/social/unreleased/> .
@prefix dlthings: <https://concepts.datalad.org/s/things/v1/> .
@prefix trr379: <https://trr379.de/> .

trr379:test_john_ttl a dlsocial:Person ;
    dlsocial:given_name "Johnöüß" ;
    dlthings:annotations [ a dlthings:Annotation ;
            dlthings:annotation_tag <http://purl.obolibrary.org/obo/NCIT_C54269> ;
            dlthings:annotation_value "test_user_1" ] .
"""

ttl_input_record = """@prefix dlsocial: <https://concepts.datalad.org/s/social/unreleased/> .
@prefix dlthings: <https://concepts.datalad.org/s/things/v1/> .
@prefix trr379: <https://trr379.de/> .

trr379:test_john_ttl a dlsocial:Person ;
    dlsocial:given_name "Johnöüß" .
"""

ttl_output_record = """@prefix dlsocial: <https://concepts.datalad.org/s/social/unreleased/> .
@prefix dlthings: <https://concepts.datalad.org/s/things/v1/> .
@prefix obo: <http://purl.obolibrary.org/obo/> .
@prefix trr379: <https://trr379.de/> .

trr379:test_john_ttl a dlsocial:Person ;
    dlsocial:given_name "Johnöüß" ;
    dlthings:annotations [ a dlthings:Annotation ;
            dlthings:annotation_tag obo:NCIT_C54269 ;
            dlthings:annotation_value "test_user_1" ] .
"""

new_json_pid = 'trr379:another_john_ttl'


def test_json_ttl_json_trr379(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Deposit JSON records
    response = test_client.post(
        '/collection_trr379/record/Person',
        headers={'x-dumpthings-token': 'token_1'},
        json=json_record,
    )
    assert response.status_code == HTTP_200_OK

    # Retrieve TTL records
    response = test_client.get(
        f'/collection_trr379/record?pid={json_record["pid"]}&format=ttl',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == HTTP_200_OK
    ttl = response.text

    # modify the pid
    ttl = ttl.replace(json_record['pid'], new_ttl_pid)

    response = test_client.post(
        '/collection_trr379/record/Person?format=ttl',
        headers={'content-type': 'text/turtle', 'x-dumpthings-token': 'token_1'},
        data=ttl,
    )
    assert response.status_code == HTTP_200_OK

    # Retrieve JSON record
    response = test_client.get(
        f'/collection_trr379/record?pid={new_ttl_pid}&format=json',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == HTTP_200_OK
    json_object = cleaned_json(response.json(), remove_keys=('annotations',))
    assert json_object != json_record
    json_object['pid'] = json_record['pid']
    assert json_object == json_record


def test_ttl_json_ttl_trr379(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Deposit a ttl record
    response = test_client.post(
        '/collection_trr379/record/Person?format=ttl',
        headers={
            'x-dumpthings-token': 'token_1',
            'content-type': 'text/turtle',
        },
        data=ttl_input_record,
    )
    assert response.status_code == HTTP_200_OK

    # Retrieve JSON records
    response = test_client.get(
        '/collection_trr379/record?pid=trr379:test_john_ttl&format=json',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == HTTP_200_OK
    json_object = response.json()

    # modify the pid
    json_object['pid'] = new_json_pid

    response = test_client.post(
        '/collection_trr379/record/Person?format=json',
        headers={'x-dumpthings-token': 'token_1'},
        json=json_object,
    )
    assert response.status_code == HTTP_200_OK

    # Retrieve ttl record
    response = test_client.get(
        f'/collection_trr379/record?pid={new_json_pid}&format=ttl',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert response.status_code == HTTP_200_OK
    assert (
        response.text.strip()
        == ttl_output_record.replace('trr379:test_john_ttl', new_json_pid).strip()
    )
