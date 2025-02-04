from enum import Enum
from typing import Union


class Format(str, Enum):
    json = 'json'
    ttl = 'ttl'


YAML = Union[int, float, str, dict, list, None]

JSON = Union[dict, list, str, int, float, None]
