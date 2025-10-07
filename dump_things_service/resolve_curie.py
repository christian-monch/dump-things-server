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
    curie_or_iri: str,
) -> str:
    if ':' not in curie_or_iri:
        return curie_or_iri

    if not is_curie(curie_or_iri):
        return curie_or_iri

    prefix, identifier = curie_or_iri.split(':', 1)
    prefix_value = model.linkml_meta.root.get('prefixes', {}).get(prefix)
    if prefix_value is None:
        msg = (
            f'cannot resolve CURIE "{curie_or_iri}". No such prefix: "{prefix}" in '
            f'schema: {model.linkml_meta.root["id"]}'
        )
        raise CurieResolutionError(msg)

    return prefix_value['prefix_reference'] + identifier


def is_curie(
    curie_or_iri: str,
):
    if ':' not in curie_or_iri:
        return False

    return url_regex.match(curie_or_iri) is None
