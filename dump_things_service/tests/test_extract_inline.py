from __future__ import annotations

import dataclasses
import sys
from copy import copy
from typing import TYPE_CHECKING

import pytest  # noqa F401

from dump_things_service import HTTP_200_OK
from dump_things_service.record import RecordDirStore
from dump_things_service.utils import cleaned_json

if TYPE_CHECKING:
    from pydantic import BaseModel

    from dump_things_service import JSON


@dataclasses.dataclass
class Thing:
    pid: str
    relations: dict[str, Thing] | None = None

    def model_copy(self):
        return copy(self)


@dataclasses.dataclass
class Agent(Thing):
    acted_on_behalf_of: list[str] | None = None


@dataclasses.dataclass
class InstantaneousEvent(Thing):
    at_time: str | None = None


@dataclasses.dataclass
class Person(Agent):
    given_name: str | None = None


class MockedModule:
    Agent = Agent
    Thing = Thing
    Person = Person
    InstantaneousEvent = InstantaneousEvent


def get_inlined_object(model_module):
    return model_module.Person(
        pid='trr379:test_extract_1',
        given_name='Grandfather',
        relations={
            'trr379:test_extract_1_1': model_module.Person(
                pid='trr379:test_extract_1_1',
                given_name='Father',
                relations={
                    'trr379:test_extract_1_1_1': model_module.Agent(
                        pid='trr379:test_extract_1_1_1',
                        acted_on_behalf_of=['trr379:test_extract_1_1'],
                    ),
                },
            ),
            'trr379:test_extract_1_2': model_module.InstantaneousEvent(
                pid='trr379:test_extract_1_2',
                at_time='2028-12-31',
            ),
        },
    )


inlined_object = get_inlined_object(sys.modules[__name__])
inlined_json_record = cleaned_json(dataclasses.asdict(inlined_object))


empty_inlined_object = Person(
    pid='trr379:test_extract_a',
    given_name='Opa',
    relations={
        'trr379:test_extract_a_a': Thing(pid='trr379:test_extract_a_a'),
        'trr379:test_extract_a_b': Thing(pid='trr379:test_extract_a_b'),
        'trr379:test_extract_a_c': Thing(pid='trr379:test_extract_a_c'),
    },
)

empty_inlined_json_record = cleaned_json(dataclasses.asdict(empty_inlined_object))


tree = (
    ('trr379:test_extract_1', ('trr379:test_extract_1_1', 'trr379:test_extract_1_2')),
    ('trr379:test_extract_1_1', ('trr379:test_extract_1_1_1',)),
    ('trr379:test_extract_1_2', ()),
    ('trr379:test_extract_1_1_1', ()),
)


ttl_with_inline_a = """
@prefix dlsocial: <https://concepts.datalad.org/s/social/unreleased/> .
@prefix dlthings: <https://concepts.datalad.org/s/things/v1/> .
@prefix trr379: <https://trr379.de/> .

trr379:test_ttl_inline_1 a dlsocial:Person ;
    dlsocial:given_name "Grandfather" ;
    dlthings:relation trr379:test_ttl_inline_1_1,
        trr379:test_ttl_inline_1_2 .
"""

ttl_with_inline_b = """
@prefix dlprov: <https://concepts.datalad.org/s/prov/unreleased/> .
@prefix trr379: <https://trr379.de/> .

trr379:test_ttl_inline_1_1_1 a dlprov:Agent ;
    dlprov:acted_on_behalf_of trr379:test_ttl_inline_1_1 .
"""

ttl_with_inline_c = """
@prefix dltemporal: <https://concepts.datalad.org/s/temporal/unreleased/> .
@prefix trr379: <https://trr379.de/> .
@prefix w3ctr: <https://www.w3.org/TR/> .

trr379:test_ttl_inline_1_2 a dltemporal:InstantaneousEvent ;
    dltemporal:at_time "2028-12-31"^^w3ctr:NOTE-datetime .
"""

ttl_with_inline_d = """
@prefix dlsocial: <https://concepts.datalad.org/s/social/unreleased/> .
@prefix dlthings: <https://concepts.datalad.org/s/things/v1/> .
@prefix trr379: <https://trr379.de/> .

trr379:test_ttl_inline_1_1 a dlsocial:Person ;
    dlsocial:given_name "Father" ;
    dlthings:relation trr379:test_ttl_inline_1_1_1 .

"""

ttls_with_inline = (
    ('Person', ttl_with_inline_a),
    ('Agent', ttl_with_inline_b),
    ('InstantaneousEvent', ttl_with_inline_c),
    ('Person', ttl_with_inline_d),
)

ttl_tree = (
    ('trr379:test_ttl_inline_1', ('trr379:test_ttl_inline_1_1', 'trr379:test_ttl_inline_1_2')),
    ('trr379:test_ttl_inline_1_1', ('trr379:test_ttl_inline_1_1_1',)),
    ('trr379:test_ttl_inline_1_2', ()),
    ('trr379:test_ttl_inline_1_1_1', ()),
)


def test_inline_extraction_locally(dump_stores_simple):
    root = dump_stores_simple

    store = RecordDirStore(
        root=root / 'collection_1' / 'token_1',
        model=MockedModule(),
        pid_mapping_function=None,
        suffix='yaml',
    )
    records = store.extract_inlined(inlined_object, 'hans')
    _check_result_objects(records, tree)


def _check_result_objects(
    records: list[BaseModel],
    tree: tuple[tuple[str, tuple[str, ...]]],
):
    def get_record_by_pid(record_pid: str):
        for record in records:
            if record.pid == record_pid:
                return record
        return None

    for record_pid, linked_pids in tree:
        record = get_record_by_pid(record_pid)
        assert len(record.relations or {}) == len(linked_pids)
        for linked_pid in linked_pids:
            # Processing might add `schema_type` to records, ignore it.
            assert record.relations[linked_pid].pid == linked_pid


def test_dont_extract_empty_things_locally(dump_stores_simple):
    root = dump_stores_simple

    store = RecordDirStore(
        root=root / 'collection_1' / 'token_1',
        model=MockedModule(),
        pid_mapping_function=None,
        suffix='yaml',
    )
    records = store.extract_inlined(empty_inlined_object, 'dieter')
    assert len(records) == 1
    assert records[0] == empty_inlined_object


def test_inline_extraction_on_service(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Deposit JSON record
    response = test_client.post(
        '/collection_trr379/record/Person',
        headers={'x-dumpthings-token': 'token_1'},
        json=inlined_json_record,
    )
    assert response.status_code == HTTP_200_OK
    # Check linkage between records
    _check_result_json(response.json(), tree)

    # Verify that the records are actually stored individually and can be
    # retrieved by their pid.
    records = []
    for record_pid in (entry[0] for entry in tree):
        response = test_client.get(
            f'/collection_trr379/record?pid={record_pid}',
            headers={'x-dumpthings-token': 'token_1'},
        )
        assert response.status_code == HTTP_200_OK
        records.append(response.json())

    # Check linkage between records
    _check_result_json(records, tree)

    # Check that individual record classes were recognized
    for class_name, pids in (
        ('Person', ('trr379:test_extract_1', 'trr379:test_extract_1_1')),
        ('Agent', ('trr379:test_extract_1_1_1',)),
        ('InstantaneousEvent', ('trr379:test_extract_1_2',)),
    ):
        records = test_client.get(
            f'/collection_trr379/records/{class_name}',
            headers={'x-dumpthings-token': 'token_1'},
        ).json()
        for pid in pids:
            assert any(record['pid'] == pid for record in records)


def test_inline_ttl_processing(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    # Deposit TTL records
    for class_name, ttl_record in ttls_with_inline:
        response = test_client.post(
            f'/collection_trr379/record/{class_name}?format=ttl',
            headers={'x-dumpthings-token': 'token_1'},
            json=ttl_record,
        )
        assert response.status_code == HTTP_200_OK

    # Verify that the records are actually stored individually and can be
    # retrieved by their pid.
    records = []
    for record_pid in (entry[0] for entry in ttl_tree):
        response = test_client.get(
            f'/collection_trr379/record?pid={record_pid}',
            headers={'x-dumpthings-token': 'token_1'},
        )
        assert response.status_code == HTTP_200_OK
        records.append(response.json())

    # Check linkage between records
    _check_result_json(records, ttl_tree)

    # Check that individual record classes were recognized
    for class_name, pids in (
        ('Person', ('trr379:test_ttl_inline_1', 'trr379:test_ttl_inline_1_1')),
        ('Agent', ('trr379:test_ttl_inline_1_1_1',)),
        ('InstantaneousEvent', ('trr379:test_ttl_inline_1_2',)),
    ):
        records = test_client.get(
            f'/collection_trr379/records/{class_name}',
            headers={'x-dumpthings-token': 'token_1'},
        ).json()
        for pid in pids:
            assert any(record['pid'] == pid for record in records)


def _check_result_json(
    records: list[JSON],
    tree: tuple[tuple[str, tuple[str, ...]]],
):
    def get_record_by_pid(record_pid: str):
        for record in records:
            if record['pid'] == record_pid:
                return record
        return None

    for record_pid, linked_pids in tree:
        record = get_record_by_pid(record_pid)
        if 'relations' in record:
            assert len(record['relations']) == len(linked_pids)
        for linked_pid in linked_pids:
            # Processing might add `schema_type` to records, ignore it.
            if 'schema_type' in record['relations'][linked_pid]:
                del record['relations'][linked_pid]['schema_type']
            assert record['relations'][linked_pid] == {'pid': linked_pid}


def test_dont_extract_empty_things_on_service(fastapi_client_simple):
    test_client, store = fastapi_client_simple

    # Deposit JSON record
    response = test_client.post(
        '/collection_trr379/record/Person',
        headers={'x-dumpthings-token': 'token_1'},
        json=empty_inlined_json_record,
    )
    assert response.status_code == HTTP_200_OK

    # Ensure that no `Thing` records are extracted
    thing_path = store / 'token_stores' / 'token_1' / 'collection_trr379' / 'Thing'
    assert tuple(thing_path.rglob('*.yaml')) == ()
