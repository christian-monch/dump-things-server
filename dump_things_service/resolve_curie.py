from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import types


def resolve_curie(
    model: types.ModuleType,
    curie: str,
) -> str:
    if ":" not in curie:
        return curie

    if curie.startswith(('http://', 'https://')):
        return curie

    prefix, identifier = curie.split(':', 1)
    prefix_value = model.linkml_meta.root.get('prefixes', {}).get(prefix)
    if prefix_value is None:
        return curie
    return prefix_value['prefix_reference'] + identifier
