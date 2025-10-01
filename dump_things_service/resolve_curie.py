from __future__ import annotations

import re
from typing import TYPE_CHECKING

from dump_things_service.exceptions import CurieResolutionError

if TYPE_CHECKING:
    import types

# The libraries accept a string that starts with "schema-name" plus "://" as
# an URI. Strings with ':' that do not match the pattern are considered to
# have a prefix.
url_pattern = '^[^:]*://'
url_regex = re.compile(url_pattern)


def resolve_curie(
    model: types.ModuleType,
    curie: str,
) -> str:
    if ':' not in curie:
        return curie

    if url_regex.match(curie):
        return curie

    prefix, identifier = curie.split(':', 1)
    prefix_value = model.linkml_meta.root.get('prefixes', {}).get(prefix)
    if prefix_value is None:
        msg = (
            f'cannot resolve CURIE "{curie}". No such prefix: "{prefix}" in '
            f'schema: {model.linkml_meta.root["id"]}'
        )
        raise CurieResolutionError(msg)

    return prefix_value['prefix_reference'] + identifier
