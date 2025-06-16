import strawberry
from typing import NewType, Optional

NodeUriOrCurie = strawberry.scalar(NewType("NodeUriOrCurie", object), serialize=lambda v: v, parse_value=lambda v: v)

Uri = strawberry.scalar(NewType("Uri", object), serialize=lambda v: v, parse_value=lambda v: v)

Uriorcurie = strawberry.scalar(NewType("Uriorcurie", object), serialize=lambda v: v, parse_value=lambda v: v)

W3CISO8601 = strawberry.scalar(NewType("W3CISO8601", object), serialize=lambda v: v, parse_value=lambda v: v)

HexBinary = strawberry.scalar(NewType("HexBinary", object), serialize=lambda v: v, parse_value=lambda v: v)

NonNegativeInteger = strawberry.scalar(NewType("NonNegativeInteger", object), serialize=lambda v: v, parse_value=lambda v: v)

@strawberry.type
class AccessMethod:
    schema_type: NodeUriOrCurie | None

@strawberry.type
class AccessThroughLandingPage:
    schema_type: NodeUriOrCurie | None
    landing_page: Uri | None

@strawberry.type
class Annotation:
    annotation_tag: 'Thing'
    annotation_value: str | None

@strawberry.interface
class ThingMixin:
    annotations: list[Annotation | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    description: str | None
    exact_mappings: list[Uriorcurie | None] | None
    attributes: list[Optional['AttributeSpecification']] | None
    characterized_by: list[Optional['Statement']] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None

@strawberry.type
class ValueSpecificationMixin:
    range: Uriorcurie | None
    value: str | None

@strawberry.type
class Checksum:
    schema_type: NodeUriOrCurie | None
    creator: Uriorcurie
    notation: HexBinary

@strawberry.type
class ComputedIdentifier:
    creator: Uriorcurie | None
    notation: str
    schema_type: NodeUriOrCurie | None

@strawberry.type
class DataService:
    pid: Uriorcurie
    relations: list[Optional['Thing']] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
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
    pid: Uriorcurie
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
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
    download_urls: list[Uri | None] | None

@strawberry.type
class Distribution:
    pid: Uriorcurie
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
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
    pid: Uriorcurie
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
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
    creator: Uriorcurie | None
    notation: str
    schema_agency: str | None

@strawberry.type
class ElectronicDistribution:
    pid: Uriorcurie
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
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
    pid: Uriorcurie
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None
    attributed_to: list[Agent | None] | None
    derived_from: list[Entity | None] | None
    generated_by: list[Activity | None] | None

@strawberry.type
class Grant:
    pid: Uriorcurie
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
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
    pid: Uriorcurie
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    acted_on_behalf_of: list[Agent | None] | None
    at_location: Location | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None

@strawberry.type
class Identifier:
    creator: Uriorcurie | None
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
    pid: Uriorcurie
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    at_time: W3CISO8601 | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None

@strawberry.type
class Instrument:
    pid: Uriorcurie
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
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
    creator: Uriorcurie | None
    notation: str
    schema_type: NodeUriOrCurie | None
    schema_agency: str | None

@strawberry.type
class Location:
    pid: Uriorcurie
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None

@strawberry.type
class Organization:
    pid: Uriorcurie
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    acted_on_behalf_of: list[Agent | None] | None
    at_location: Location | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None
    name: str | None
    short_name: str | None

@strawberry.type
class Person:
    pid: Uriorcurie
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
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
    pid: Uriorcurie
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
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
    pid: Uriorcurie
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None

@strawberry.type
class Publication:
    pid: Uriorcurie
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
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
    pid: Uriorcurie
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
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
    pid: Uriorcurie
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None

@strawberry.type
class SoftwareAgent:
    pid: Uriorcurie
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
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
class Activity:
    pid: Uriorcurie
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
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
    pid: Uriorcurie
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    acted_on_behalf_of: list[Agent | None] | None
    at_location: Location | None
    identifiers: list[Identifier | None] | None
    qualified_relations: list[Relationship | None] | None

@strawberry.type
class TransientRelationship:
    object: Thing
    roles: list[Role | None] | None
    schema_type: NodeUriOrCurie | None
    started_at: W3CISO8601 | None
    ended_at: W3CISO8601 | None

@strawberry.type
class Thing(ThingMixin):
    pid: Uriorcurie
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None

@strawberry.type
class AttributeSpecification(ThingMixin, ValueSpecificationMixin):
    predicate: Property
    annotations: list['Annotation' | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    description: str | None
    exact_mappings: list[Uriorcurie | None] | None
    attributes: list['AttributeSpecification' | None] | None
    characterized_by: list['Statement' | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    range: Uriorcurie | None
    value: str | None

@strawberry.type
class ValueSpecification(ValueSpecificationMixin):
    pid: Uriorcurie
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    description: str | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[Uriorcurie | None] | None
    close_mappings: list[Uriorcurie | None] | None
    broad_mappings: list[Uriorcurie | None] | None
    narrow_mappings: list[Uriorcurie | None] | None
    related_mappings: list[Uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    value: str
    range: Uriorcurie | None
