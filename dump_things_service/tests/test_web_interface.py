"""Faulty input test for the Web interface"""

from itertools import product

import pytest

from . import HTTP_500_INTERNAL_SERVER_ERROR

store_names = ('store_1', 'xasdasd', '../../../abc')
class_names = ('Thing', 'Mosdlkjsdfnmxcfd', '../../../abc')
queries = ('format', 'somerslkhjsdfsdf')
format_names = ('json', 'ttl', 'sdfsdfkjsdkfsd')


@pytest.mark.parametrize(
    'store_name,class_name,query,format_name',  # noqa PT006
    tuple(product(*(store_names, class_names, queries, format_names))),
)
def test_web_interface_fuzzing(
    fastapi_client_simple,
    store_name,
    class_name,
    query,
    format_name,
):
    """Check that no internal server error occurs with weird input"""
    test_client, _ = fastapi_client_simple
    result = test_client.post(
        f'/{store_name}/record/{class_name}?{query}={format_name}',
        headers={'x-dumpthings-token': 'token_1'},
        json={'id': 'xyz:bbbb'},
    )
    assert result.status_code < HTTP_500_INTERNAL_SERVER_ERROR
