import strawberry
from enum import Enum
from typing import NewType

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

@strawberry.enum
class LicensedSoftware(Enum):
    adobe = "adobe"
    forklift = "forklift"
    matlab = "matlab"
    matlab_toolboxes = "matlab_toolboxes"
    msoffice = "msoffice"
    spss = "spss"
    zoom = "zoom"

@strawberry.enum
class OrganizationType(Enum):
    team = "team"
    group = "group"
    division = "division"
    institute = "institute"
    researchcenter = "researchcenter"
    researchorganization = "researchorganization"
    faculty = "faculty"
    college = "college"
    university = "university"
    nonprofit = "nonprofit"
    business = "business"

@strawberry.enum
class RequestableAccessory(Enum):
    screen_keyboard_mouse = "screen_keyboard_mouse"
    headset_std = "headset_std"
    headset_custom = "headset_custom"
    other = "other"

@strawberry.enum
class RequestableLaptop(Enum):
    mac_new_querty = "mac_new_querty"
    mac_new_quertz = "mac_new_quertz"
    mac_used_querty = "mac_used_querty"
    mac_used_quertz = "mac_used_quertz"
    lenovolinux_new_querty = "lenovolinux_new_querty"
    lenovolinux_new_quertz = "lenovolinux_new_quertz"
    lenovolinux_used_querty = "lenovolinux_used_querty"
    lenovolinux_used_quertz = "lenovolinux_used_quertz"
    other = "other"

@strawberry.enum
class UserClassification(Enum):
    inm7_fzj_employee = "inm7_fzj_employee"
    inm7_hhu_employee = "inm7_hhu_employee"
    student = "student"
    external = "external"

@strawberry.interface
class CurationAid:
    curation_comments: list[str | None] | None
    display_label: str | None
    identifiers: list[Identifier | None] | None
    record_contact: Person | None

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

@strawberry.type
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
class DOI:
    schema_type: NodeUriOrCurie | None
    creator: uriorcurie | None
    notation: str
    schema_agency: str | None

@strawberry.type
class Identifier:
    creator: uriorcurie | None
    notation: str
    schema_type: NodeUriOrCurie | None

@strawberry.type
class IssuedIdentifier:
    creator: uriorcurie | None
    notation: str
    schema_type: NodeUriOrCurie | None
    schema_agency: str | None

@strawberry.type
class JuselessAccount:
    pid: strawberry.ID
    relations: list[Thing | None] | None
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
    name: str | None
    curation_comments: list[str | None] | None
    display_label: str | None
    identifiers: list[Identifier | None] | None
    record_contact: Person | None
    member_of: list[JuselessGroup | None] | None

@strawberry.type
class JuselessGroup:
    pid: strawberry.ID
    relations: list[Thing | None] | None
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
    name: str | None
    curation_comments: list[str | None] | None
    display_label: str | None
    identifiers: list[Identifier | None] | None
    record_contact: Person | None

@strawberry.type
class Property:
    pid: strawberry.ID
    relations: list[Thing | None] | None
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
class Statement:
    object: Thing
    predicate: Property

@strawberry.type
class User:
    pid: strawberry.ID
    relations: list[Thing | None] | None
    characterized_by: list[Statement | None] | None
    attributes: list[AttributeSpecification | None] | None
    annotations: list[Annotation | None] | None
    exact_mappings: list[uriorcurie | None] | None
    close_mappings: list[uriorcurie | None] | None
    broad_mappings: list[uriorcurie | None] | None
    narrow_mappings: list[uriorcurie | None] | None
    related_mappings: list[uriorcurie | None] | None
    schema_type: NodeUriOrCurie | None
    curation_comments: list[str | None] | None
    identifiers: list[Identifier | None] | None
    record_contact: Person | None
    allocated_software_licenses: list[LicensedSoftware | None] | None
    end_date: W3CISO8601
    juseless_account: JuselessAccount | None
    requested_accessories: list[RequestableAccessory | None] | None
    requested_juseless_account_name: str | None
    juseless_group_membership: list[JuselessGroup | None] | None
    requested_laptop: RequestableLaptop | None
    start_date: W3CISO8601
    user_classifications: list[UserClassification | None]
    family_name: str
    given_name: str
    additional_names: list[str | None] | None
    honorific_name_prefix: str | None
    honorific_name_suffix: str | None
    member_of: list[Organization | None] | None
    offices: str | None
    emails: list[EmailAddress | None] | None
    orcid: str | None
    description: str | None
    display_label: str | None

@strawberry.type
class Account(CurationAid):
    pid: strawberry.ID
    relations: list[Thing | None] | None
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
    name: str | None
    curation_comments: list[str | None] | None
    display_label: str | None
    identifiers: list[Identifier | None] | None
    record_contact: Person | None

@strawberry.type
class Building(CurationAid):
    pid: strawberry.ID
    relations: list[Thing | None] | None
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
    name: str
    site: Site | None
    display_label: str | None
    curation_comments: list[str | None] | None
    identifiers: list[Identifier | None] | None
    record_contact: Person | None

@strawberry.type
class BuildingLevel(CurationAid):
    pid: strawberry.ID
    relations: list[Thing | None] | None
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
    name: str
    building: Building | None
    display_label: str | None
    curation_comments: list[str | None] | None
    identifiers: list[Identifier | None] | None
    record_contact: Person | None

@strawberry.type
class Organization(CurationAid):
    pid: strawberry.ID
    relations: list[Thing | None] | None
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
    name: str
    short_name: str | None
    parent_organization: Organization | None
    organization_type: OrganizationType | None
    leaders: list[Person | None] | None
    display_label: str | None
    curation_comments: list[str | None] | None
    identifiers: list[Identifier | None] | None
    record_contact: Person | None

@strawberry.type
class Person(CurationAid):
    pid: strawberry.ID
    relations: list[Thing | None] | None
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
    additional_names: list[str | None] | None
    family_name: str | None
    given_name: str | None
    honorific_name_prefix: str | None
    honorific_name_suffix: str | None
    emails: list[EmailAddress | None] | None
    member_of: list[Organization | None] | None
    orcid: str | None
    display_label: str | None
    curation_comments: list[str | None] | None
    identifiers: list[Identifier | None] | None
    record_contact: Person | None

@strawberry.type
class Room(CurationAid):
    pid: strawberry.ID
    relations: list[Thing | None] | None
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
    name: str
    building_level: BuildingLevel | None
    display_label: str | None
    curation_comments: list[str | None] | None
    identifiers: list[Identifier | None] | None
    record_contact: Person | None

@strawberry.type
class Site(CurationAid):
    pid: strawberry.ID
    relations: list[Thing | None] | None
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
    name: str
    display_label: str | None
    curation_comments: list[str | None] | None
    identifiers: list[Identifier | None] | None
    record_contact: Person | None

@strawberry.type
class Thing(ThingMixin):
    pid: strawberry.ID
    relations: list[Thing | None] | None
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
    relations: list[Thing | None] | None
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

