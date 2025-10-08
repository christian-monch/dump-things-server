""" Monkeypatch for linkml_runtime.utils.enumerations

Patches linkml_runtime.utils.enumerations.EnumDefinitionMeta.__getitem__
and linkml_runtime.utils.enumerations.EnumDefinitionMeta.__contains__
"""
import logging
from importlib import import_module

from jsonasobj2 import JsonObj


logger = logging.getLogger('dump_things_service')


def EnumDefinitionMeta__getitem__(cls, item):
    if isinstance(item, JsonObj):
        return cls.__dict__[item.text]
    return cls.__dict__[item]


def EnumDefinitionMeta__contains__(cls, item) -> bool:
    if isinstance(item, JsonObj):
        return item.text in cls.__dict__
    return item in cls.__dict__


logger.info('patching linkml_runtime.utils.enumerations')

mod = import_module('linkml_runtime.utils.enumerations')
mod.EnumDefinitionMeta.__getitem__ = EnumDefinitionMeta__getitem__
mod.EnumDefinitionMeta.__contains__ = EnumDefinitionMeta__contains__
