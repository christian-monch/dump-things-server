from __future__ import annotations

import json
import sys
from copy import copy
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pytest  # noqa F401
from pydantic import ValidationError

from dump_things_service.model import build_model
from dump_things_service.storage import (
    Storage,
    TokenStorage,
)

from . import HTTP_200_OK

if TYPE_CHECKING:
    from pydantic import BaseModel

    from dump_things_service import JSON


@dataclass
class Thing:
    id: str
    relations: dict[str, Thing] | None = None
    contains: list[str] | None = None

    def model_copy(self):
        return copy(self)


@dataclass
class Agent(Thing):
    acted_on_behalf_of: list[str] | None = None


@dataclass
class InstantaneousEvent(Thing):
    at_time: str | None = None


@dataclass
class Person(Thing):
    given_name: str | None = None


class MockedModule:
    Agent = Agent
    Thing = Thing
    Person = Person
    InstantaneousEvent = InstantaneousEvent


# The value is a `Person` record
inlined_json_record = {
    'id': 'trr379:test_extract_1',
    'given_name': 'Grandfather',
    'relations': {
        # The value is a `Person` record
        'trr379:test_extract_1_1': {
            'id': 'trr379:test_extract_1_1',
            'given_name': 'Father',
            'relations': {
                # The value is an `Agent` record
                'trr379:test_extract_1_1_1': {
                    'id': 'trr379:test_extract_1_1_1',
                    'acted_on_behalf_of': [
                        'trr379:test_extract_1_1',
                    ],
                },
            },
        },
        # The value is an `InstantaneousEvent` record
        'trr379:test_extract_1_2': {
            'id': 'trr379:test_extract_1_2',
            'at_time': '2028-12-31',
        },
    },
}


def get_inlined_object(model_module):
    return model_module.Person(
        id='trr379:test_extract_1',
        given_name='Grandfather',
        relations={
            'trr379:test_extract_1_1': model_module.Person(
                id='trr379:test_extract_1_1',
                given_name='Father',
                relations={
                    'trr379:test_extract_1_1_1': model_module.Agent(
                        id='trr379:test_extract_1_1_1',
                        acted_on_behalf_of=['trr379:test_extract_1_1'],
                        relations=None,
                    ),
                },
            ),
            'trr379:test_extract_1_2': model_module.InstantaneousEvent(
                id='trr379:test_extract_1_2',
                at_time='2028-12-31',
                relations=None,
            ),
        },
    )


inlined_object = get_inlined_object(sys.modules[__name__])


tree = (
    ('trr379:test_extract_1', ('trr379:test_extract_1_1', 'trr379:test_extract_1_2'), ()),
    ('trr379:test_extract_1_1', ('trr379:test_extract_1_1_1',), ()),
    ('trr379:test_extract_1_2', (), ()),
    ('trr379:test_extract_1_1_1', (), ()),
)


def test_testschema(dump_stores_simple):
    schema_path = Path(__file__).parent / 'testschema.yaml'
    model_module = build_model(str(schema_path))

    # Get an inlined object with testschema-classes and validate it
    local_inlined_object = get_inlined_object(model_module)
    x = model_module.Person.model_validate(local_inlined_object)
    print(repr(x))

    # Do the same for JSON
    x = model_module.Person.model_validate_json(json.dumps(inlined_json_record))
    print(repr(x))

    # Set the related objects to empty strings and validate it
    local_inlined_object.relations = {
        'trr379:test_extract_1_1': '',
        'trr379:test_extract_1_2': ''
    }
    x = model_module.Person.model_validate(local_inlined_object)
    print(repr(x))

    # Do the same for JSON
    old_relations = inlined_json_record['relations']
    inlined_json_record['relations'] = {
        'trr379:test_extract_1_1': '',
        'trr379:test_extract_1_2': '',
    }
    x = model_module.Person.model_validate_json(json.dumps(inlined_json_record))
    print(repr(x))
    inlined_json_record['relations'] = old_relations


def test_inline_extraction_locally(dump_stores_simple):
    root = dump_stores_simple

    store = TokenStorage(
        root / 'token_stores' / 'token_1', Storage(root / 'global_store')
    )
    records = store.extract_inlined(inlined_object, MockedModule())
    _check_result_objects(records, tree)


def _check_result_objects(
    records: list[BaseModel],
    tree: tuple[tuple[str, tuple[str, ...], tuple[str, ...]]],
):
    def get_record_by_id(record_id: str):
        for record in records:
            if record.id == record_id:
                return record
        return None

    for record_id, linked_ids, pre_existing in tree:
        record = get_record_by_id(record_id)
        for identifier in pre_existing:
            del record.relations[identifier]
        assert len(record.relations or []) == len(linked_ids)
        for linked_id in linked_ids:
            # Processing might add `schema_type` to records, ignore it.
            assert record.relations[linked_id] == ''


def test_inline_extraction_on_service(fastapi_client_simple):
    test_client, store = fastapi_client_simple

    # Deposit JSON record with extracted records
    response = test_client.post(
        '/trr379_store/record/Person',
        headers={'x-dumpthings-token': 'token_1'},
        json={
            'id': 'trr379:test_extract_two_1',
            'given_name': 'Grandfather',
            'relations': {
                'trr379:test_extract_two_1_1': '',
                'trr379:test_extract_two_1_2': '',
            },
        },
    )
    assert response.status_code == HTTP_200_OK

    # Deposit JSON record
    response = test_client.post(
        '/trr379_store/record/Person',
        headers={'x-dumpthings-token': 'token_1'},
        json=inlined_json_record,
    )
    assert response.status_code == HTTP_200_OK

    # Expect records with no inlined data but minimal `relations`-entries
    records = []
    for record_id in (entry[0] for entry in tree):
        response = test_client.get(
            f'/trr379_store/record?id={record_id}',
            headers={'x-dumpthings-token': 'token_1'},
        )
        assert response.status_code == HTTP_200_OK
        records.append(response.json())

    # Check linkage between records
    _check_result_json(records, tree)

    # Check that individual record classes are recognized
    for class_name, identifiers in (
        ('Person', ('trr379:test_extract_1', 'trr379:test_extract_1_1')),
        ('Agent', ('trr379:test_extract_1_1_1',)),
        ('InstantaneousEvent', ('trr379:test_extract_1_2',)),
    ):
        records = test_client.get(
            f'/trr379_store/records/{class_name}',
            headers={'x-dumpthings-token': 'token_1'},
        ).json()
        for identifier in identifiers:
            assert any(record['id'] == identifier for record in records)


def _check_result_json(
    records: list[JSON],
    tree: tuple[tuple[str, tuple[str, ...]]],
):
    def get_record_by_id(record_id: str):
        for record in records:
            if record['id'] == record_id:
                return record
        return None

    for record_id, linked_ids, pre_existing in tree:
        record = get_record_by_id(record_id)
        for identifier in pre_existing:
            del record['contains'][identifier]
        if linked_ids:
            assert len(record['relations']) == len(linked_ids)
            for linked_id in linked_ids:
                # Processing might add `schema_type` to records, ignore it.
                assert record['relations'][linked_id] == ''
        else:
            assert record.get('relations', None) is None
