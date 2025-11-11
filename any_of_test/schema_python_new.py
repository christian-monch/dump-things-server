# Auto generated from schema.yaml by pythongen.py version: 0.0.1
# Generation date: 2025-11-11T16:44:03
# Schema: any_of_test_schema
#
# id: http://example.org/any-of-test-schema
# description:
# license: https://creativecommons.org/publicdomain/zero/1.0/

import dataclasses
import re
from dataclasses import dataclass
from datetime import (
    date,
    datetime,
    time
)
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Union
)

from jsonasobj2 import (
    JsonObj,
    as_dict
)
from linkml_runtime.linkml_model.meta import (
    EnumDefinition,
    PermissibleValue,
    PvFormulaOptions
)
from linkml_runtime.utils.curienamespace import CurieNamespace
from linkml_runtime.utils.enumerations import EnumDefinitionImpl
from linkml_runtime.utils.formatutils import (
    camelcase,
    sfx,
    underscore
)
from linkml_runtime.utils.metamodelcore import (
    bnode,
    empty_dict,
    empty_list
)
from linkml_runtime.utils.slot import Slot
from linkml_runtime.utils.yamlutils import (
    YAMLRoot,
    extended_float,
    extended_int,
    extended_str
)
from rdflib import (
    Namespace,
    URIRef
)

from linkml_runtime.linkml_model.types import String

metamodel_version = "1.7.0"
version = None

# Namespaces
ABC = CurieNamespace('abc', 'http://example.org/person-schema/abc/')
LINKML = CurieNamespace('linkml', 'https://w3id.org/linkml/')
DEFAULT_ = ABC


# Types

# Class references



Any = Any

@dataclass(repr=False)
class Thing(YAMLRoot):
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = ABC["Thing"]
    class_class_curie: ClassVar[str] = "abc:Thing"
    class_name: ClassVar[str] = "Thing"
    class_model_uri: ClassVar[URIRef] = ABC.Thing

    pid: Optional[str] = None
    multislot: Optional[list[Union["ClassA", "ClassB"]]] = empty_list()

    def __post_init__(self, *_: str, **kwargs: Any):
        if self.pid is not None and not isinstance(self.pid, str):
            self.pid = str(self.pid)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class ClassA(YAMLRoot):
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = ABC["ClassA"]
    class_class_curie: ClassVar[str] = "abc:ClassA"
    class_name: ClassVar[str] = "ClassA"
    class_model_uri: ClassVar[URIRef] = ABC.ClassA

    pid: Optional[str] = None
    name_a: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self.pid is not None and not isinstance(self.pid, str):
            self.pid = str(self.pid)

        if self.name_a is not None and not isinstance(self.name_a, str):
            self.name_a = str(self.name_a)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class ClassB(YAMLRoot):
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = ABC["ClassB"]
    class_class_curie: ClassVar[str] = "abc:ClassB"
    class_name: ClassVar[str] = "ClassB"
    class_model_uri: ClassVar[URIRef] = ABC.ClassB

    pid: Optional[str] = None
    name_b: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self.pid is not None and not isinstance(self.pid, str):
            self.pid = str(self.pid)

        if self.name_b is not None and not isinstance(self.name_b, str):
            self.name_b = str(self.name_b)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class ClassC(YAMLRoot):
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = ABC["ClassC"]
    class_class_curie: ClassVar[str] = "abc:ClassC"
    class_name: ClassVar[str] = "ClassC"
    class_model_uri: ClassVar[URIRef] = ABC.ClassC

    pid: Optional[str] = None
    name_c: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self.pid is not None and not isinstance(self.pid, str):
            self.pid = str(self.pid)

        if self.name_c is not None and not isinstance(self.name_c, str):
            self.name_c = str(self.name_c)

        super().__post_init__(**kwargs)


# Enumerations


# Slots
class slots:
    pass

slots.pid = Slot(uri=ABC.pid, name="pid", curie=ABC.curie('pid'),
                   model_uri=ABC.pid, domain=None, range=Optional[str])

slots.name_a = Slot(uri=ABC.name_a, name="name_a", curie=ABC.curie('name_a'),
                   model_uri=ABC.name_a, domain=None, range=Optional[str])

slots.name_b = Slot(uri=ABC.name_b, name="name_b", curie=ABC.curie('name_b'),
                   model_uri=ABC.name_b, domain=None, range=Optional[str])

slots.name_c = Slot(uri=ABC.name_c, name="name_c", curie=ABC.curie('name_c'),
                   model_uri=ABC.name_c, domain=None, range=Optional[str])

slots.multislot = Slot(uri=ABC.multislot, name="multislot", curie=ABC.curie('multislot'),
                   model_uri=ABC.multislot, domain=None, range=Optional[list[Union["ClassA", "ClassB"]]])

