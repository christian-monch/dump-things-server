from __future__ import annotations

import re
import sys
from datetime import (
    date,
    datetime,
    time
)
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    ClassVar,
    Literal,
    Optional,
    Union
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_validator
)


metamodel_version = "None"
version = "None"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        validate_assignment = True,
        validate_default = True,
        extra = "forbid",
        arbitrary_types_allowed = True,
        use_enum_values = True,
        strict = False,
    )
    pass




class LinkMLMeta(RootModel):
    root: dict[str, Any] = {}
    model_config = ConfigDict(frozen=True)

    def __getattr__(self, key:str):
        return getattr(self.root, key)

    def __getitem__(self, key:str):
        return self.root[key]

    def __setitem__(self, key:str, value):
        self.root[key] = value

    def __contains__(self, key:str) -> bool:
        return key in self.root


linkml_meta = LinkMLMeta({'default_prefix': 'abc',
     'default_range': 'string',
     'id': 'http://example.org/any-of-test-schema',
     'imports': ['linkml:types'],
     'name': 'any_of_test_schema',
     'prefixes': {'abc': {'prefix_prefix': 'abc',
                          'prefix_reference': 'http://example.org/person-schema/abc/'},
                  'linkml': {'prefix_prefix': 'linkml',
                             'prefix_reference': 'https://w3id.org/linkml/'}},
     'source_file': 'schema.yaml'} )


# CM >>>>>>
from linkml_runtime.utils.curienamespace import CurieNamespace
from rdflib import (
    Namespace,
    URIRef
)

ABC = CurieNamespace('abc', 'http://example.org/person-schema/abc/')
LINKML = CurieNamespace('linkml', 'https://w3id.org/linkml/')
DEFAULT_ = ABC
# CM <<<<


class Thing(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'http://example.org/any-of-test-schema'})

    class_class_uri: ClassVar[URIRef] = ABC["Thing"]
    class_class_curie: ClassVar[str] = "abc:Thing"
    class_name: ClassVar[str] = "Thing"
    class_model_uri: ClassVar[URIRef] = ABC.Thing

    pid: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'pid', 'domain_of': ['Thing', 'ClassA', 'ClassB', 'ClassC']} })
    multislot: Optional[list[Union[ClassA, ClassB]]] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'multislot',
         'any_of': [{'range': 'ClassA'}, {'range': 'ClassB'}],
         'domain_of': ['Thing']} })


class ClassA(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'http://example.org/any-of-test-schema'})

    class_class_uri: ClassVar[URIRef] = ABC["ClassA"]
    class_class_curie: ClassVar[str] = "abc:ClassA"
    class_name: ClassVar[str] = "ClassA"
    class_model_uri: ClassVar[URIRef] = ABC.ClassA


    pid: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'pid', 'domain_of': ['Thing', 'ClassA', 'ClassB', 'ClassC']} })
    name_a: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'name_a', 'domain_of': ['ClassA']} })


class ClassB(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'http://example.org/any-of-test-schema'})

    class_class_uri: ClassVar[URIRef] = ABC["ClassB"]
    class_class_curie: ClassVar[str] = "abc:ClassB"
    class_name: ClassVar[str] = "ClassB"
    class_model_uri: ClassVar[URIRef] = ABC.ClassB

    pid: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'pid', 'domain_of': ['Thing', 'ClassA', 'ClassB', 'ClassC']} })
    name_b: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'name_b', 'domain_of': ['ClassB']} })


class ClassC(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'http://example.org/any-of-test-schema'})

    pid: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'pid', 'domain_of': ['Thing', 'ClassA', 'ClassB', 'ClassC']} })
    name_c: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'name_c', 'domain_of': ['ClassC']} })


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
Thing.model_rebuild()
ClassA.model_rebuild()
ClassB.model_rebuild()
ClassC.model_rebuild()
