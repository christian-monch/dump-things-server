from __future__ import annotations

from typing import TYPE_CHECKING

from dump_things_service.exceptions import CurieResolutionError

if TYPE_CHECKING:
    import types


def resolve_curie(
    model: types.ModuleType,
    curie: str,
) -> str:
    if ':' not in curie:
        return curie

    if (
        curie.startswith(('http://', 'https://'))
        or (curie[0] == '<' and curie[-1] == '>')
        or (curie[0] == '[' and curie[-1] == ']')
    ):
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
