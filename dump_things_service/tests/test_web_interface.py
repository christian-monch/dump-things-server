"""Faulty input test for the Web interface"""

from itertools import product

import pytest

from .. import HTTP_500_INTERNAL_SERVER_ERROR

collection_names = ('collection_1', 'xasdasd', '../../../abc')
class_names = ('Thing', 'Mosdlkjsdfnmxcfd', '../../../abc')
queries = ('format', 'somerslkhjsdfsdf')
format_names = ('json', 'ttl', 'sdfsdfkjsdkfsd')
pids = ('', '--------', '&&&&&', 'abc', 'abc&', 'abc&format=ttl')


@pytest.mark.parametrize(
    'collection_name,class_name,query,format_name',  # noqa PT006
    tuple(product(*(collection_names, class_names, queries, format_names))),
)
def test_web_interface_post_errors(
    fastapi_client_simple,
    collection_name,
    class_name,
    query,
    format_name,
):
    """Check that no internal server error occurs with weird input"""
    test_client, _ = fastapi_client_simple
    result = test_client.post(
        f'/{collection_name}/record/{class_name}?{query}={format_name}',
        headers={'x-dumpthings-token': 'token_1'},
        json={'pid': 'xyz:web_interface_test_pid0x123123'},
    )
    assert result.status_code < HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.parametrize(
    'collection_name,class_name,query,format_name',  # noqa PT006
    tuple(product(*(collection_names, class_names, queries, format_names))),
)
def test_web_interface_get_class_errors(
    fastapi_client_simple,
    collection_name,
    class_name,
    query,
    format_name,
):
    """Check that no internal server error occurs with weird input"""
    test_client, _ = fastapi_client_simple
    result = test_client.get(
        f'/{collection_name}/records/{class_name}?{query}={format_name}',
    )
    assert result.status_code < HTTP_500_INTERNAL_SERVER_ERROR

    result = test_client.get(
        f'/{collection_name}/record/{class_name}?{query}={format_name}',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert result.status_code < HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.parametrize(
    'collection_name,pid,query,format_name',  # noqa PT006
    tuple(product(*(collection_names, pids, queries, format_names))),
)
def test_web_interface_get_pid_errors(
    fastapi_client_simple,
    collection_name,
    pid,
    query,
    format_name,
):
    """Check that no internal server error occurs with weird input"""
    test_client, _ = fastapi_client_simple
    result = test_client.get(
        f'/{collection_name}/records?{pid}&{query}={format_name}',
    )
    assert result.status_code < HTTP_500_INTERNAL_SERVER_ERROR

    result = test_client.get(
        f'/{collection_name}/records?{pid}&{query}={format_name}',
        headers={'x-dumpthings-token': 'token_1'},
    )
    assert result.status_code < HTTP_500_INTERNAL_SERVER_ERROR
