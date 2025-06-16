from __future__ import annotations

import strawberry
from enum import Enum
from typing import Annotated
from typing import NewType
from typing import Union

AllThings = Annotated[
    Union[
        'Thing',
        'Role',
        'Person',
        'Group',
        'Organization',
        'Project',
        'Publication',
        'Resource',
        'Dataset',
        'Distribution',
        'Document',
        'Grant',
        'Instrument',
        'ElectronicDistribution',
        'DataService',
        'Property',
        'ValueSpecification',
        'Agent',
        'Activity',
        'Entity',
        'SoftwareAgent',
        'InstantaneousEvent',
        'Location'
    ],
    strawberry.union(name="AllThings")
]

curie = strawberry.scalar(NewType("curie", object), serialize=lambda v: v, parse_value=lambda v: v)

date = strawberry.scalar(NewType("date", object), serialize=lambda v: v, parse_value=lambda v: v)

date_or_datetime = strawberry.scalar(NewType("date_or_datetime", object), serialize=lambda v: v, parse_value=lambda v: v)

datetime = strawberry.scalar(NewType("datetime", object), serialize=lambda v: v, parse_value=lambda v: v)

decimal = strawberry.scalar(NewType("decimal", object), serialize=lambda v: v, parse_value=lambda v: v)

double = strawberry.scalar(NewType("double", object), serialize=lambda v: v, parse_value=lambda v: v)

EmailAddress = strawberry.scalar(NewType("EmailAddress", object), serialize=lambda v: v, parse_value=lambda v: v)

HexBinary = strawberry.scalar(NewType("HexBinary", object), serialize=lambda v: v, parse_value=lambda v: v)

jsonpath = strawberry.scalar(NewType("jsonpath", object), serialize=lambda v: v, parse_value=lambda v: v)

jsonpointer = strawberry.scalar(NewType("jsonpointer", object), serialize=lambda v: v, parse_value=lambda v: v)

ncname = strawberry.scalar(NewType("ncname", object), serialize=lambda v: v, parse_value=lambda v: v)

nodeidentifier = strawberry.scalar(NewType("nodeidentifier", object), serialize=lambda v: v, parse_value=lambda v: v)

NodeUriOrCurie = strawberry.scalar(NewType("NodeUriOrCurie", object), serialize=lambda v: v, parse_value=lambda v: v)

NonNegativeInteger = strawberry.scalar(NewType("NonNegativeInteger", object), serialize=lambda v: v, parse_value=lambda v: v)

objectidentifier = strawberry.scalar(NewType("objectidentifier", object), serialize=lambda v: v, parse_value=lambda v: v)

sparqlpath = strawberry.scalar(NewType("sparqlpath", object), serialize=lambda v: v, parse_value=lambda v: v)

time = strawberry.scalar(NewType("time", object), serialize=lambda v: v, parse_value=lambda v: v)

uri = strawberry.scalar(NewType("uri", object), serialize=lambda v: v, parse_value=lambda v: v)

uriorcurie = strawberry.scalar(NewType("uriorcurie", object), serialize=lambda v: v, parse_value=lambda v: v)

W3CISO8601 = strawberry.scalar(NewType("W3CISO8601", object), serialize=lambda v: v, parse_value=lambda v: v)

@strawberry.type
class AccessMethod:
    schema_type: NodeUriOrCurie | None

@strawberry.type
class AccessThroughLandingPage:
    schema_type: NodeUriOrCurie | None
    landing_page: uri | None

@strawberry.type
class Activity:
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    at_location: Location | None
    ended_at: W3CISO8601 | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None
    started_at: W3CISO8601 | None
    associated_with: list[Agent | None] | None
    informed_by: list[Activity | None] | None

@strawberry.type
class Agent:
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    acted_on_behalf_of: list[Agent | None] | None
    at_location: Location | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None

@strawberry.type
class Annotation:
    annotation_tag: Thing
    annotation_value: str | None

@strawberry.interface
class ThingMixin:
    annotations: list[Annotation | None] | None
    broad_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    description: str | None
    exact_mappings: list[uriorcurie | None] | None
    attributes: list[AttributeSpecification | None] | None
    characterized_by: list[Statement | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None

@strawberry.interface
class ValueSpecificationMixin:
    range: uriorcurie | None
    value: str | None

@strawberry.type
class Checksum:
    schema_type: NodeUriOrCurie | None
    creator: uriorcurie
    notation: HexBinary

@strawberry.type
class ComputedIdentifier:
    creator: uriorcurie | None
    notation: str
    schema_type: NodeUriOrCurie | None

@strawberry.type
class DataService:
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None
    attributed_to: list[Agent | None] | None
    derived_from: list[Entity | None] | None
    generated_by: list[Activity | None] | None
    about: list[Thing | None] | None
    access_methods: list[AccessMethod | None] | None
    conforms_to: Thing | None
    date_modified: W3CISO8601 | None
    date_published: W3CISO8601 | None
    keywords: list[str | None] | None
    previous_version: Resource | None
    same_as: Thing | None
    short_name: str | None
    title: str | None
    version_label: str | None
    version_notes: list[str | None] | None

@strawberry.type
class DataServiceAccess:
    schema_type: NodeUriOrCurie | None
    data_service: DataService
    locator: str

@strawberry.type
class Dataset:
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None
    attributed_to: list[Agent | None] | None
    derived_from: list[Entity | None] | None
    generated_by: list[Activity | None] | None
    about: list[Thing | None] | None
    access_methods: list[AccessMethod | None] | None
    conforms_to: Thing | None
    date_modified: W3CISO8601 | None
    date_published: W3CISO8601 | None
    keywords: list[str | None] | None
    previous_version: Resource | None
    same_as: Thing | None
    short_name: str | None
    title: str | None
    version_label: str | None
    version_notes: list[str | None] | None
    distributions: list[Distribution | None] | None

@strawberry.type
class DirectDownload:
    schema_type: NodeUriOrCurie | None
    download_urls: list[uri | None] | None

@strawberry.type
class Distribution:
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None
    attributed_to: list[Agent | None] | None
    derived_from: list[Entity | None] | None
    generated_by: list[Activity | None] | None
    about: list[Thing | None] | None
    access_methods: list[AccessMethod | None] | None
    conforms_to: Thing | None
    date_modified: W3CISO8601 | None
    date_published: W3CISO8601 | None
    keywords: list[str | None] | None
    same_as: Thing | None
    short_name: str | None
    title: str | None
    version_label: str | None
    version_notes: list[str | None] | None
    distribution_of: Resource | None
    previous_version: Distribution | None

@strawberry.type
class Document:
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None
    attributed_to: list[Agent | None] | None
    derived_from: list[Entity | None] | None
    generated_by: list[Activity | None] | None
    about: list[Thing | None] | None
    access_methods: list[AccessMethod | None] | None
    conforms_to: Thing | None
    date_modified: W3CISO8601 | None
    date_published: W3CISO8601 | None
    keywords: list[str | None] | None
    previous_version: Resource | None
    same_as: Thing | None
    short_name: str | None
    title: str | None
    version_label: str | None
    version_notes: list[str | None] | None
    distributions: list[Distribution | None] | None

@strawberry.type
class DOI:
    schema_type: NodeUriOrCurie | None
    creator: uriorcurie | None
    notation: str
    schema_agency: str | None

@strawberry.type
class ElectronicDistribution:
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None
    attributed_to: list[Agent | None] | None
    derived_from: list[Entity | None] | None
    generated_by: list[Activity | None] | None
    about: list[Thing | None] | None
    access_methods: list[AccessMethod | None] | None
    conforms_to: Thing | None
    date_modified: W3CISO8601 | None
    date_published: W3CISO8601 | None
    keywords: list[str | None] | None
    same_as: Thing | None
    short_name: str | None
    title: str | None
    version_label: str | None
    version_notes: list[str | None] | None
    distribution_of: Resource | None
    byte_size: NonNegativeInteger | None
    checksums: list[Checksum | None] | None
    format: Thing | None
    media_type: str | None
    previous_version: ElectronicDistribution | None

@strawberry.type
class Entity:
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None
    attributed_to: list[Agent | None] | None
    derived_from: list[Entity | None] | None
    generated_by: list[Activity | None] | None

@strawberry.type
class Grant:
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None
    attributed_to: list[Agent | None] | None
    derived_from: list[Entity | None] | None
    generated_by: list[Activity | None] | None
    about: list[Thing | None] | None
    access_methods: list[AccessMethod | None] | None
    conforms_to: Thing | None
    date_modified: W3CISO8601 | None
    date_published: W3CISO8601 | None
    keywords: list[str | None] | None
    previous_version: Resource | None
    same_as: Thing | None
    short_name: str | None
    title: str | None
    version_label: str | None
    version_notes: list[str | None] | None
    sponsor: Agent | None

@strawberry.type
class Group:
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    acted_on_behalf_of: list[Agent | None] | None
    at_location: Location | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None

@strawberry.type
class Identifier:
    creator: uriorcurie | None
    notation: str
    schema_type: NodeUriOrCurie | None

@strawberry.type
class IndexedResourcePart:
    roles: list[Role | None] | None
    schema_type: NodeUriOrCurie | None
    locator: str
    object: Resource

@strawberry.type
class IndexedResourcePartOf:
    roles: list[Role | None] | None
    schema_type: NodeUriOrCurie | None
    locator: str
    object: Resource

@strawberry.type
class IndexedResourceRelationship:
    roles: list[Role | None] | None
    schema_type: NodeUriOrCurie | None
    locator: str
    object: Resource

@strawberry.type
class InstantaneousEvent:
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    at_time: W3CISO8601 | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None

@strawberry.type
class Instrument:
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None
    attributed_to: list[Agent | None] | None
    derived_from: list[Entity | None] | None
    generated_by: list[Activity | None] | None
    about: list[Thing | None] | None
    access_methods: list[AccessMethod | None] | None
    conforms_to: Thing | None
    date_modified: W3CISO8601 | None
    date_published: W3CISO8601 | None
    keywords: list[str | None] | None
    previous_version: Resource | None
    same_as: Thing | None
    short_name: str | None
    title: str | None
    version_label: str | None
    version_notes: list[str | None] | None

@strawberry.type
class IssuedIdentifier:
    creator: uriorcurie | None
    notation: str
    schema_type: NodeUriOrCurie | None
    schema_agency: str | None

@strawberry.type
class Location:
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None

@strawberry.type
class Organization:
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    acted_on_behalf_of: list[Agent | None] | None
    at_location: Location | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None
    name: str | None
    short_name: str | None

@strawberry.type
class Person:
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    acted_on_behalf_of: list[Agent | None] | None
    at_location: Location | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None
    additional_names: list[str | None] | None
    family_name: str | None
    given_name: str | None
    honorific_name_prefix: str | None
    honorific_name_suffix: str | None
    formatted_name: str | None

@strawberry.type
class PersonalRequest:
    schema_type: NodeUriOrCurie | None
    description: str | None

@strawberry.type
class Project:
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    at_location: Location | None
    ended_at: W3CISO8601 | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None
    started_at: W3CISO8601 | None
    associated_with: list[Agent | None] | None
    informed_by: list[Activity | None] | None
    short_name: str | None
    title: str | None

@strawberry.type
class Property:
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None

@strawberry.type
class Publication:
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None
    attributed_to: list[Agent | None] | None
    derived_from: list[Entity | None] | None
    generated_by: list[Activity | None] | None
    about: list[Thing | None] | None
    access_methods: list[AccessMethod | None] | None
    conforms_to: Thing | None
    keywords: list[str | None] | None
    previous_version: Resource | None
    same_as: Thing | None
    short_name: str | None
    title: str | None
    version_label: str | None
    version_notes: list[str | None] | None
    date_modified: W3CISO8601 | None
    date_published: W3CISO8601 | None

@strawberry.type
class Relationship:
    object: Thing
    roles: list[Role | None] | None
    schema_type: NodeUriOrCurie | None

@strawberry.type
class Resource:
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None
    attributed_to: list[Agent | None] | None
    derived_from: list[Entity | None] | None
    generated_by: list[Activity | None] | None
    about: list[Thing | None] | None
    access_methods: list[AccessMethod | None] | None
    conforms_to: Thing | None
    date_modified: W3CISO8601 | None
    date_published: W3CISO8601 | None
    keywords: list[str | None] | None
    previous_version: Resource | None
    same_as: Thing | None
    short_name: str | None
    title: str | None
    version_label: str | None
    version_notes: list[str | None] | None

@strawberry.type
class Role:
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None

@strawberry.type
class SoftwareAgent:
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    acted_on_behalf_of: list[Agent | None] | None
    at_location: Location | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None

@strawberry.type
class Statement:
    object: Thing
    predicate: Property

@strawberry.type
class TransientRelationship:
    object: Thing
    roles: list[Role | None] | None
    schema_type: NodeUriOrCurie | None
    started_at: W3CISO8601 | None
    ended_at: W3CISO8601 | None

@strawberry.enum
class ClassNames(Enum):
    AccessMethod = "AccessMethod"
    AccessThroughLandingPage = "AccessThroughLandingPage"
    Activity = "Activity"
    Agent = "Agent"
    Annotation = "Annotation"
    AttributeSpecification = "AttributeSpecification"
    Checksum = "Checksum"
    ComputedIdentifier = "ComputedIdentifier"
    DOI = "DOI"
    DataService = "DataService"
    DataServiceAccess = "DataServiceAccess"
    Dataset = "Dataset"
    DirectDownload = "DirectDownload"
    Distribution = "Distribution"
    Document = "Document"
    ElectronicDistribution = "ElectronicDistribution"
    Entity = "Entity"
    Grant = "Grant"
    Group = "Group"
    Identifier = "Identifier"
    IndexedResourcePart = "IndexedResourcePart"
    IndexedResourcePartOf = "IndexedResourcePartOf"
    IndexedResourceRelationship = "IndexedResourceRelationship"
    InstantaneousEvent = "InstantaneousEvent"
    Instrument = "Instrument"
    IssuedIdentifier = "IssuedIdentifier"
    Location = "Location"
    Organization = "Organization"
    Person = "Person"
    PersonalRequest = "PersonalRequest"
    Project = "Project"
    Property = "Property"
    Publication = "Publication"
    Relationship = "Relationship"
    Resource = "Resource"
    Role = "Role"
    SoftwareAgent = "SoftwareAgent"
    Statement = "Statement"
    Thing = "Thing"
    TransientRelationship = "TransientRelationship"
    ValueSpecification = "ValueSpecification"


@strawberry.type
class Thing(ThingMixin):
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None

@strawberry.type
class AttributeSpecification(ThingMixin, ValueSpecificationMixin):
    predicate: Property
    annotations: list[Annotation | None] | None
    broad_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    description: str | None
    exact_mappings: list[uriorcurie | None] | None
    attributes: list[AttributeSpecification | None] | None
    characterized_by: list[Statement | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    range: uriorcurie | None
    value: str | None

@strawberry.type
class ValueSpecification(ValueSpecificationMixin):
    pid: strawberry.ID
    relations: list[AllThings] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    value: str
    range: uriorcurie | None


def resolve_pid(pid: str) -> AllThings:
    """
    Resolve a PID to the corresponding object.
    This is a placeholder and should be replaced with actual logic.
    """
    return Person(
        pid=strawberry.ID(pid),
        relations=None,
        characterized_by=None,
        attributes=None,
        description=None,
        annotations=None,
        exact_mappings=None,
        close_mappings=None,
        broad_mappings=None,
        narrow_mappings=None,
        related_mappings=None,
        schema_type='dlsocial:Person',
        acted_on_behalf_of=None,
        at_location=None,
        identifiers=None,
        qualified_relations=None,
        additional_names=None,
        family_name=f'Müller-{pid}',
        given_name=f'hans-{pid}',
        honorific_name_prefix=None,
        honorific_name_suffix=None,
        formatted_name=f'hans-{pid} Müller',
    )

@strawberry.type
class Query:
    record: AllThings | None = strawberry.field(resolver=resolve_pid)
    records: list[AllThings]

schema = strawberry.Schema(query=Query)
