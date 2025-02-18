""" Faulty input test for the Web interface
"""
import random
from itertools import product

import pytest   # noqa F401 -- needed for pytest fixtures

from hypothesis import (
    assume,
    given,
    strategies as st,
)

from dump_things_service.tests.fixtures import fastapi_client_simple


store_names = ('store_1', 'xasdasd', '../../../abc')
class_names = ('Thing', 'Mosdlkjsdfnmxcfd', '../../../abc')
queries = ('format', 'somerslkhjsdfsdf')
format_names = ('json', 'ttl', 'sdfsdfkjsdkfsd')


@pytest.mark.parametrize(
    'store_name,class_name,query,format_name',
    tuple(product(*(store_names, class_names, queries, format_names)))
)
def test_web_interface_fuzzing(
    fastapi_client_simple,
    store_name,
    class_name,
    query,
    format_name,
):
    """ Check that no internal server error occurs with weird input"""
    test_client, _ = fastapi_client_simple
    result = test_client.post(
        f'/{store_name}/record/{class_name}?{query}={format_name}',
        headers={'x-dumpthings-token': 'token_1'},
        json={'id': 'xyz:bbbb'},
    )
    assert result.status_code < 500 or result.status_code >= 600
