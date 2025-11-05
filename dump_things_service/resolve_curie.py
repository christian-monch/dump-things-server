from __future__ import annotations

import re
from typing import TYPE_CHECKING

from linkml_runtime import SchemaView

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
            f"cannot resolve CURIE '{curie_or_iri}'. No such prefix: '{prefix}' in "
            f'schema: {model.linkml_meta.root["id"]}'
        )
        raise CurieResolutionError(msg)

    return prefix_value['prefix_reference'] + identifier


def is_curie(
    curie_or_iri: str,
) -> bool:
    if ':' not in curie_or_iri:
        return False
    return not is_uri(curie_or_iri)


def is_uri(
        curie_or_iri: str,
) -> bool:
    return url_regex.match(curie_or_iri) is not None


def get_curie(
        schemaview: SchemaView,
        name_curie_or_uri: str,
) -> str:
    if is_uri(name_curie_or_uri):
        x = schemaview.namespaces().curie_for(name_curie_or_uri)
        return x

    return ensure_prefix(schemaview, name_curie_or_uri)


def get_uri(
        schemaview: SchemaView,
        name_curie_or_uri: str,
) -> str:
    if is_uri(name_curie_or_uri):
        return name_curie_or_uri

    name_curie_or_uri = ensure_prefix(schemaview, name_curie_or_uri)
    x = schemaview.namespaces().uri_for(name_curie_or_uri)
    return x


def ensure_prefix(
        schemaview: SchemaView,
        name: str,
) -> str:

    if ':' not in name:
        default_prefix = schemaview.schema.default_prefix
        if default_prefix is None:
            raise ValueError('default prefix missing')
        return default_prefix + ':' + name
