from __future__ import annotations

import dataclasses
import sys
from copy import copy
from pathlib import Path
from typing import TYPE_CHECKING

import pytest  # F401

from dump_things_service import HTTP_200_OK
from dump_things_service.patches import (
    enabled,  # noqa: F401 -- tests need patching, which is a side effect of the import
)
from dump_things_service.store.model_store import ModelStore
from dump_things_service.utils import cleaned_json

if TYPE_CHECKING:
    from pydantic import BaseModel

    from dump_things_service import JSON


# Path to a local simple test schema
schema_path = Path(__file__).parent / 'testschema.yaml'


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
        pid='dlflatsocial:test_extract_1',
        given_name='Grandfather',
        relations={
            'dlflatsocial:test_extract_1_1': model_module.Person(
                pid='dlflatsocial:test_extract_1_1',
                given_name='Father',
                relations={
                    'dlflatsocial:test_extract_1_1_1': model_module.Agent(
                        pid='dlflatsocial:test_extract_1_1_1',
                        acted_on_behalf_of=['dlflatsocial:test_extract_1_1'],
                    ),
                },
            ),
            'dlflatsocial:test_extract_1_2': model_module.InstantaneousEvent(
                pid='dlflatsocial:test_extract_1_2',
                at_time='2028-12-31',
            ),
        },
    )


inlined_object = get_inlined_object(sys.modules[__name__])
inlined_json_record = cleaned_json(dataclasses.asdict(inlined_object))


empty_inlined_object = Person(
    pid='dlflatsocial:test_extract_a',
    given_name='Opa',
    relations={
        'dlflatsocial:test_extract_a_a': Thing(pid='dlflatsocial:test_extract_a_a'),
        'dlflatsocial:test_extract_a_b': Thing(pid='dlflatsocial:test_extract_a_b'),
        'dlflatsocial:test_extract_a_c': Thing(pid='dlflatsocial:test_extract_a_c'),
    },
)

empty_inlined_json_record = cleaned_json(dataclasses.asdict(empty_inlined_object))


tree = (
    ('dlflatsocial:test_extract_1', ('dlflatsocial:test_extract_1_1', 'dlflatsocial:test_extract_1_2')),
    ('dlflatsocial:test_extract_1_1', ('dlflatsocial:test_extract_1_1_1',)),
    ('dlflatsocial:test_extract_1_2', ()),
    ('dlflatsocial:test_extract_1_1_1', ()),
)


ttl_with_inline_a = """
@prefix dlsocialmx: <https://concepts.datalad.org/s/social-mixin/unreleased/> .
@prefix dlthings: <https://concepts.datalad.org/s/things/v1/> .
@prefix dlflatsocial <https://concepts.datalad.org/s/flat-social/unreleased/> .

dlflatsocial:test_ttl_inline_1 a dlsocial:Person ;
    dlsocialmx:given_name "Grandfather" ;
    dlthings:relation dlflatsocial:test_ttl_inline_1_1,
        dlflatsocial:test_ttl_inline_1_2 .
"""

ttl_with_inline_b = """
@prefix dlprov: <https://concepts.datalad.org/s/prov/unreleased/> .
@prefix dlflatsocial <https://trr379.de/> .

dlflatsocial:test_ttl_inline_1_1_1 a dlprov:Agent ;
    dlprov:acted_on_behalf_of dlflatsocial:test_ttl_inline_1_1 .
"""

ttl_with_inline_c = """
@prefix dltemporal: <https://concepts.datalad.org/s/temporal/unreleased/> .
@prefix dlflatsocial <https://concepts.datalad.org/s/flat-social/unreleased/> .
@prefix w3ctr: <https://www.w3.org/TR/> .

dlflatsocial:test_ttl_inline_1_2 a dltemporal:InstantaneousEvent ;
    dltemporal:at_time "2028-12-31"^^w3ctr:NOTE-datetime .
"""

ttl_with_inline_d = """
@prefix dlsocialmx: <https://concepts.datalad.org/s/social-mixin/unreleased/> .
@prefix dlthings: <https://concepts.datalad.org/s/things/v1/> .
@prefix dlflatsocial <https://trr379.de/> .

dlflatsocial:test_ttl_inline_1_1 a dlsocial:Person ;
    dlsocialmx:given_name "Father" ;
    dlthings:relation dlflatsocial:test_ttl_inline_1_1_1 .

"""

ttls_with_inline = (
    ('Person', ttl_with_inline_a),
    ('Agent', ttl_with_inline_b),
    ('InstantaneousEvent', ttl_with_inline_c),
    ('Person', ttl_with_inline_d),
)

ttl_tree = (
    (
        'dlflatsocial:test_ttl_inline_1',
        ('dlflatsocial:test_ttl_inline_1_1', 'dlflatsocial:test_ttl_inline_1_2'),
    ),
    ('dlflatsocial:test_ttl_inline_1_1', ('dlflatsocial:test_ttl_inline_1_1_1',)),
    ('dlflatsocial:test_ttl_inline_1_2', ()),
    ('dlflatsocial:test_ttl_inline_1_1_1', ()),
)


def test_inline_extraction_locally():
    store = ModelStore(
        schema=str(schema_path),
        backend=None,
    )
    store.model = MockedModule()
    records = store.extract_inlined(inlined_object)
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


def test_dont_extract_empty_things_locally():
    store = ModelStore(
        schema=str(schema_path),
        backend=None,
    )
    store.model = MockedModule()
    records = store.extract_inlined(empty_inlined_object)
    assert len(records) == 1
    assert records[0] == empty_inlined_object


# We skip this test because the dlflatsocial-schema does not support inlined
# relations
@pytest.mark.xfail
def test_inline_extraction_on_service(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    for i in range(1, 3):
        # Deposit JSON record
        response = test_client.post(
            f'/collection_dlflatsocial-{i}/record/Person',
            headers={'x-dumpthings-token': 'token_1'},
            json=inlined_json_record,
        )
        assert response.status_code == HTTP_200_OK, 'Response content:' + response.text
        # Check linkage between records
        _check_result_json(response.json(), tree)

        # Verify that the records are actually stored individually and can be
        # retrieved by their pid.
        records = []
        for record_pid in (entry[0] for entry in tree):
            response = test_client.get(
                f'/collection_dlflatsocial-{i}/record?pid={record_pid}',
                headers={'x-dumpthings-token': 'token_1'},
            )
            assert response.status_code == HTTP_200_OK
            records.append(response.json())

        # Check linkage between records
        _check_result_json(records, tree)

        # Check that individual record classes were recognized
        for class_name, pids in (
            ('Person', ('dlflatsocial:test_extract_1', 'dlflatsocial:test_extract_1_1')),
            ('Agent', ('dlflatsocial:test_extract_1_1_1',)),
            ('InstantaneousEvent', ('dlflatsocial:test_extract_1_2',)),
        ):
            records = test_client.get(
                f'/collection_dlflatsocial-{i}/records/{class_name}',
                headers={'x-dumpthings-token': 'token_1'},
            ).json()
            for pid in pids:
                assert any(record['pid'] == pid for record in records)


# We skip this test because the dlflatsocial-schema does not support inlined
# relations
@pytest.mark.xfail
def test_inline_ttl_processing(fastapi_client_simple):
    test_client, _ = fastapi_client_simple

    for i in range(1, 3):
        # Deposit TTL records
        for class_name, ttl_record in ttls_with_inline:
            response = test_client.post(
                f'/collection_dlflatsocial-{i}/record/{class_name}?format=ttl',
                headers={'x-dumpthings-token': 'token_1'},
                json=ttl_record,
            )
            assert response.status_code == HTTP_200_OK

        # Verify that the records are actually stored individually and can be
        # retrieved by their pid.
        records = []
        for record_pid in (entry[0] for entry in ttl_tree):
            response = test_client.get(
                f'/collection_dlflatsocial-{i}/record?pid={record_pid}',
                headers={'x-dumpthings-token': 'token_1'},
            )
            assert response.status_code == HTTP_200_OK
            records.append(response.json())

        # Check linkage between records
        _check_result_json(records, ttl_tree)

        # Check that individual record classes were recognized
        for class_name, pids in (
            ('Person', ('dlflatsocial:test_ttl_inline_1', 'dlflatsocial:test_ttl_inline_1_1')),
            ('Agent', ('dlflatsocial:test_ttl_inline_1_1_1',)),
            ('InstantaneousEvent', ('dlflatsocial:test_ttl_inline_1_2',)),
        ):
            records = test_client.get(
                f'/collection_dlflatsocial-{i}/records/{class_name}',
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

    for i in range(1, 3):
        # Deposit JSON record
        response = test_client.post(
            f'/collection_dlflatsocial-{i}/record/Person',
            headers={'x-dumpthings-token': 'token_1'},
            json=empty_inlined_json_record,
        )
        assert response.status_code == HTTP_200_OK
