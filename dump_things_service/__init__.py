from enum import Enum
from typing import (
    Any,
    Union,
)

from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

__all__ = [
    'Format',
    'HTTP_200_OK',
    'HTTP_400_BAD_REQUEST',
    'HTTP_401_UNAUTHORIZED',
    'HTTP_403_FORBIDDEN',
    'HTTP_404_NOT_FOUND',
    'HTTP_500_INTERNAL_SERVER_ERROR',
    'JSON',
    'YAML',
    'config_file_name',
]


class Format(str, Enum):
    json = 'json'
    ttl = 'ttl'


JSON = Union[dict[str, Any], list[Any], str, int, float, None]
YAML = JSON

config_file_name = '.dumpthings.yaml'
