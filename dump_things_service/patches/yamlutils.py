""" Monkeypatch for linkml_runtime.utils.yamlutil.YAMLRoot._normalize_inlined

Corresponds to the patch `patches/linkml_runtime_utils_yamlutils.diff` in the
`datalad-concepts` repository, i.e.,
<https://github.com/psychoinformatics-de/datalad-concepts.git>
"""

from copy import copy
from importlib import import_module
from typing import (
    Any,
    Optional,
    Union,
)

from jsonasobj2 import (
    JsonObj,
    JsonObjTypes,
    as_dict,
)
from linkml_runtime.utils.formatutils import items
from linkml_runtime.utils.yamlutils import (
    TypedNode,
    YAMLRoot,
)

YAMLObjTypes = Union[JsonObjTypes, "YAMLRoot"]

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    pass



def _normalize_inlined(self, slot_name: str, slot_type: type, key_name: str, keyed: bool, is_list: bool) \
        -> None:
    """
     __post_init__ function for a list of inlined keyed or identified classes.

    The input to this is either a list or dictionary of dictionaries.  In the list case, every key entry
    in the list must be unique.  In the dictionary case, the key may or may not be repeated in the dictionary
    element. The internal storage structure is a dictionary of dictionaries.
    @param slot_name: Name of the slot being normalized
    @param slot_type: Slot range type
    @param key_name: Name of the key or identifier in the range
    @param keyed: True means each identifier must be unique
    @param is_list: True means inlined as list
    """
    raw_slot: Union[list, dict, JsonObj] = self[slot_name]
    if raw_slot is None:
        raw_slot = []
    elif not isinstance(raw_slot, (dict, list, JsonObj)):
        raw_slot = [raw_slot]
    cooked_slot = list() if is_list else dict()
    cooked_keys = set()

    def order_up(key: Any, cooked_entry: YAMLRoot) -> None:
        """ A cooked entry is ready to be added to the return slot """
        if cooked_entry[key_name] != key:
            raise ValueError(
                f"Slot: {loc(slot_name)} - attribute {loc(key_name)} " \
                f"value ({loc(cooked_entry[key_name])}) does not match key ({loc(key)})")
        if keyed and key in cooked_keys:
            raise ValueError(f"{loc(key)}: duplicate key")
        cooked_keys.add(key)
        if is_list:
            cooked_slot.append(cooked_entry)
        else:
            cooked_slot[key] = cooked_entry

    def loc(s):
        loc_str = TypedNode.yaml_loc(s) if isinstance(s, TypedNode) else ''
        if loc_str == ': ':
            loc_str = ''
        return loc_str + str(s)

    def form_1(entries: dict[Any, Optional[Union[dict, JsonObj]]]) -> None:
        """ A dictionary of key:dict entries where key is the identifier and dict is an instance of slot_type """
        for key, raw_obj in items(entries):
            if raw_obj is None:
                raw_obj = {}
            if key_name not in raw_obj:
                raw_obj = copy(raw_obj)
                raw_obj[key_name] = key
            if not issubclass(type(raw_obj), slot_type):
                order_up(key, slot_type(**as_dict(raw_obj)))
            else:
                order_up(key, raw_obj)

    # TODO: Make an external function extract a root JSON list
    if isinstance(raw_slot, JsonObj):
        raw_slot = raw_slot._hide_list()

    if isinstance(raw_slot, list):
        # We have a list of entries
        for list_entry in raw_slot:
            if isinstance(list_entry, slot_type):
                order_up(list_entry[key_name], list_entry)
            elif isinstance(list_entry, (dict, JsonObj)):
                # list_entry is either a key:dict, key_name:value or **kwargs
                if len(list_entry) == 1:
                    # key:dict or key_name:key
                    for lek, lev in items(list_entry):
                        if lek == key_name and not isinstance(lev, (list, dict, JsonObj)):
                            # key_name:value
                            order_up(list_entry[lek], slot_type(**list_entry))
                            break   # Not strictly necessary, but
                        elif not isinstance(lev, (list, dict, JsonObj)):
                            # key: value --> slot_type(key, value)
                            order_up(lek, slot_type(lek, lev))
                        else:
                            form_1(list_entry)
                else:
                    # **kwargs
                    cooked_obj = slot_type(**as_dict(list_entry))
                    order_up(cooked_obj[key_name], cooked_obj)
            elif isinstance(list_entry, list):
                # *args
                cooked_obj = slot_type(*list_entry)
                order_up(cooked_obj[key_name], cooked_obj)
            else:
                # lone key [key1: , key2: ... }
                order_up(list_entry, slot_type(**{key_name: list_entry}))
    elif key_name in raw_slot and raw_slot[key_name] is not None \
                and not isinstance(raw_slot[key_name], (list, dict, JsonObj)):
        # Vanilla dictionary - {key: v11, s12: v12, ...}
        order_up(raw_slot[key_name], slot_type(**as_dict(raw_slot)))
    else:
        # We have either {key1: {obj1}, key2: {obj2}...} or {key1:, key2:, ...}
        for k, v in items(raw_slot):
            if v is None:
                v = dict()
            if isinstance(v, slot_type):
                order_up(k, v)
            elif isinstance(v, (dict, JsonObj)):
                form_1({k: v})
            elif not isinstance(v, list):
                order_up(k, slot_type(*[k, v]))
            else:
                raise ValueError(f"Unrecognized entry: {loc(k)}: {v!s}")
    self[slot_name] = cooked_slot


mod = import_module('linkml_runtime.utils.yamlutils')
mod.YAMLRoot._normalize_inlined = _normalize_inlined
