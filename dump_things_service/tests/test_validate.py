
from dump_things_service import HTTP_422_UNPROCESSABLE_CONTENT

json_records = [
    ({'name': 'Henry', 'pid': 'unknown_prefix:henry'}, HTTP_422_UNPROCESSABLE_CONTENT),
    ({'given_name': 'Henry', 'pid': 'unknown_prefix:henry'}, HTTP_422_UNPROCESSABLE_CONTENT),
    ({'given_name': 'Henry', 'pid': 'xyz:henry'}, 200),
]

ttl_records = [
    (
        """
@prefix abc: <http://example.org/person-schema/abc/> .
@prefix xyz: <https://www.example.com/xyz/> .

xyz:henry a abc:Person ;
    abc:given_name "Henry" .
""",
        200,
    ),
    (
        # Faulty class id
        """
@prefix abc: <http://example.org/person-schema/abc/> .
@prefix xyz: <https://www.example.com/xyz/> .

xyz:henry a xyz:Person ;
    abc:given_name "Henry" .
""",
        422,
    ),
    (
        # Faulty attribute id
        """
@prefix abc: <http://example.org/person-schema/abc/> .
@prefix xyz: <https://www.example.com/xyz/> .

xyz:henry a abc:Person ;
    xyz:given_name "Henry" .
""",
        422,
    ),
]


def test_validate_record(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    for record, expected_status in json_records:
        response = test_client.post(
            '/collection_1/validate/record/Person',
            headers={'x-dumpthings-token': 'token-1'},
            json=record,
        )
        assert response.status_code == expected_status, response.text

    for record, expected_status in ttl_records:
        response = test_client.post(
            '/collection_1/validate/record/Person?format=ttl',
            headers={'x-dumpthings-token': 'token-1'},
            json=record,
        )
        assert response.status_code == expected_status, response.text
