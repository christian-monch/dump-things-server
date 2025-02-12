from enum import Enum
from typing import (
    Any,
    Union,
)


class Format(str, Enum):
    json = 'json'
    ttl = 'ttl'


JSON = Union[dict[str, Any], list[Any], str, int, float, None]
YAML = JSON
