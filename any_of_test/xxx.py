# Auto generated from schema2.yaml by pythongen.py version: 0.0.1
# Generation date: 2025-11-11T15:15:58
# Schema: person_schema
#
# id: http://example.org/person-schema
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

from linkml_runtime.linkml_model.types import String, Uriorcurie
from linkml_runtime.utils.metamodelcore import URIorCURIE

metamodel_version = "1.7.0"
version = None

# Namespaces
ABC = CurieNamespace('abc', 'http://example.org/person-schema/abc/')
DLFLATSOCIAL = CurieNamespace('dlflatsocial', 'https://concepts.datalad.org/s/flat-social/unreleased/')
LINKML = CurieNamespace('linkml', 'https://w3id.org/linkml/')
OXO = CurieNamespace('oxo', 'http://purl.obolibrary.org/obo/')
SCHEMA = CurieNamespace('schema', 'http://schema.org/')
SHEX = CurieNamespace('shex', 'http://www.w3.org/ns/shex#')
TRR379 = CurieNamespace('trr379', 'http://example.org/person-schema/trr379/')
XSD = CurieNamespace('xsd', 'http://www.w3.org/2001/XMLSchema#')
XYZ = CurieNamespace('xyz', 'http://example.org/person-schema/xyz/')
DEFAULT_ = ABC


# Types

# Class references
class ThingPid(URIorCURIE):
    pass


class AnnotationAnnotationTag(ThingPid):
    pass


class BemerkungBemerkungId(ThingPid):
    pass


class AgentPid(ThingPid):
    pass


class InstantaneousEventPid(ThingPid):
    pass


class PersonPid(AgentPid):
    pass


Any = Any

@dataclass(repr=False)
class Thing(YAMLRoot):
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = ABC["Thing"]
    class_class_curie: ClassVar[str] = "abc:Thing"
    class_name: ClassVar[str] = "Thing"
    class_model_uri: ClassVar[URIRef] = ABC.Thing

    pid: Union[str, ThingPid] = None
    relations: Optional[Union[dict[Union[str, ThingPid], Union[dict, "Thing"]], list[Union[dict, "Thing"]]]] = empty_dict()
    annotations: Optional[Union[Union[dict, Any], list[Union[dict, Any]]]] = empty_list()
    schema_type: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.pid):
            self.MissingRequiredField("pid")
        if not isinstance(self.pid, ThingPid):
            self.pid = ThingPid(self.pid)

        self._normalize_inlined_as_dict(slot_name="relations", slot_type=Thing, key_name="pid", keyed=True)

        if self.schema_type is not None and not isinstance(self.schema_type, str):
            self.schema_type = str(self.schema_type)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class Annotation(YAMLRoot):
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = ABC["Annotation"]
    class_class_curie: ClassVar[str] = "abc:Annotation"
    class_name: ClassVar[str] = "Annotation"
    class_model_uri: ClassVar[URIRef] = ABC.Annotation

    annotation_tag: Union[str, AnnotationAnnotationTag] = None
    annotation_value: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.annotation_tag):
            self.MissingRequiredField("annotation_tag")
        if not isinstance(self.annotation_tag, AnnotationAnnotationTag):
            self.annotation_tag = AnnotationAnnotationTag(self.annotation_tag)

        if self.annotation_value is not None and not isinstance(self.annotation_value, str):
            self.annotation_value = str(self.annotation_value)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class Bemerkung(YAMLRoot):
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = ABC["Bemerkung"]
    class_class_curie: ClassVar[str] = "abc:Bemerkung"
    class_name: ClassVar[str] = "Bemerkung"
    class_model_uri: ClassVar[URIRef] = ABC.Bemerkung

    bemerkung_id: Union[str, BemerkungBemerkungId] = None
    bemerkung_inhalt: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.bemerkung_id):
            self.MissingRequiredField("bemerkung_id")
        if not isinstance(self.bemerkung_id, BemerkungBemerkungId):
            self.bemerkung_id = BemerkungBemerkungId(self.bemerkung_id)

        if self.bemerkung_inhalt is not None and not isinstance(self.bemerkung_inhalt, str):
            self.bemerkung_inhalt = str(self.bemerkung_inhalt)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class Agent(Thing):
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = ABC["Agent"]
    class_class_curie: ClassVar[str] = "abc:Agent"
    class_name: ClassVar[str] = "Agent"
    class_model_uri: ClassVar[URIRef] = ABC.Agent

    pid: Union[str, AgentPid] = None
    acted_on_behalf_of: Optional[Union[str, list[str]]] = empty_list()

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.pid):
            self.MissingRequiredField("pid")
        if not isinstance(self.pid, AgentPid):
            self.pid = AgentPid(self.pid)

        if not isinstance(self.acted_on_behalf_of, list):
            self.acted_on_behalf_of = [self.acted_on_behalf_of] if self.acted_on_behalf_of is not None else []
        self.acted_on_behalf_of = [v if isinstance(v, str) else str(v) for v in self.acted_on_behalf_of]

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class InstantaneousEvent(Thing):
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = ABC["InstantaneousEvent"]
    class_class_curie: ClassVar[str] = "abc:InstantaneousEvent"
    class_name: ClassVar[str] = "InstantaneousEvent"
    class_model_uri: ClassVar[URIRef] = ABC.InstantaneousEvent

    pid: Union[str, InstantaneousEventPid] = None
    at_time: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.pid):
            self.MissingRequiredField("pid")
        if not isinstance(self.pid, InstantaneousEventPid):
            self.pid = InstantaneousEventPid(self.pid)

        if self.at_time is not None and not isinstance(self.at_time, str):
            self.at_time = str(self.at_time)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class Person(Agent):
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = ABC["Person"]
    class_class_curie: ClassVar[str] = "abc:Person"
    class_name: ClassVar[str] = "Person"
    class_model_uri: ClassVar[URIRef] = ABC.Person

    pid: Union[str, PersonPid] = None
    given_name: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.pid):
            self.MissingRequiredField("pid")
        if not isinstance(self.pid, PersonPid):
            self.pid = PersonPid(self.pid)

        if self.given_name is not None and not isinstance(self.given_name, str):
            self.given_name = str(self.given_name)

        super().__post_init__(**kwargs)


# Enumerations


# Slots
class slots:
    pass

slots.pid = Slot(uri=ABC.pid, name="pid", curie=ABC.curie('pid'),
                   model_uri=ABC.pid, domain=None, range=URIRef)

slots.relations = Slot(uri=ABC.relations, name="relations", curie=ABC.curie('relations'),
                   model_uri=ABC.relations, domain=None, range=Optional[Union[dict[Union[str, ThingPid], Union[dict, Thing]], list[Union[dict, Thing]]]])

slots.acted_on_behalf_of = Slot(uri=ABC.acted_on_behalf_of, name="acted_on_behalf_of", curie=ABC.curie('acted_on_behalf_of'),
                   model_uri=ABC.acted_on_behalf_of, domain=None, range=Optional[Union[str, list[str]]])

slots.annotations = Slot(uri=ABC.annotations, name="annotations", curie=ABC.curie('annotations'),
                   model_uri=ABC.annotations, domain=None, range=Optional[Union[Union[dict, Any], list[Union[dict, Any]]]])

slots.annotation_tag = Slot(uri=ABC.annotation_tag, name="annotation_tag", curie=ABC.curie('annotation_tag'),
                   model_uri=ABC.annotation_tag, domain=None, range=Optional[Union[str, ThingPid]])

slots.annotation_value = Slot(uri=ABC.annotation_value, name="annotation_value", curie=ABC.curie('annotation_value'),
                   model_uri=ABC.annotation_value, domain=None, range=Optional[str])

slots.bemerkung_id = Slot(uri=ABC.bemerkung_id, name="bemerkung_id", curie=ABC.curie('bemerkung_id'),
                   model_uri=ABC.bemerkung_id, domain=None, range=Optional[Union[str, ThingPid]])

slots.bemerkung_inhalt = Slot(uri=ABC.bemerkung_inhalt, name="bemerkung_inhalt", curie=ABC.curie('bemerkung_inhalt'),
                   model_uri=ABC.bemerkung_inhalt, domain=None, range=Optional[str])

slots.thing__schema_type = Slot(uri=ABC.schema_type, name="thing__schema_type", curie=ABC.curie('schema_type'),
                   model_uri=ABC.thing__schema_type, domain=None, range=Optional[str])

slots.instantaneousEvent__at_time = Slot(uri=ABC.at_time, name="instantaneousEvent__at_time", curie=ABC.curie('at_time'),
                   model_uri=ABC.instantaneousEvent__at_time, domain=None, range=Optional[str])

slots.person__given_name = Slot(uri=ABC.given_name, name="person__given_name", curie=ABC.curie('given_name'),
                   model_uri=ABC.person__given_name, domain=None, range=Optional[str])

slots.Annotation_annotation_tag = Slot(uri=ABC.annotation_tag, name="Annotation_annotation_tag", curie=ABC.curie('annotation_tag'),
                   model_uri=ABC.Annotation_annotation_tag, domain=Annotation, range=Union[str, AnnotationAnnotationTag])

slots.Bemerkung_bemerkung_id = Slot(uri=ABC.bemerkung_id, name="Bemerkung_bemerkung_id", curie=ABC.curie('bemerkung_id'),
                   model_uri=ABC.Bemerkung_bemerkung_id, domain=Bemerkung, range=Union[str, BemerkungBemerkungId])

