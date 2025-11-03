from __future__ import annotations

from typing import Union
#from schema_python import Thing
from dataclasses import dataclass, asdict as dataclass_asdict
from dataclass_wizard import asdict, fromdict, LoadMeta

from linkml_runtime.utils.schemaview import SchemaView


#sv = SchemaView('schema.yaml')


json_obj_1 = {
    "pid": "thing_1",
    "multislot": [],
}

json_obj_2 = {
    "pid": "thing_2",
    "multislot": [
        {
            "__tag__": "ClassA",
            "pid": "pid_a_1",
            "name_a": "name_a_1"
        },
        {
            "__tag__": "ClassA",
            "pid": "pid_a_2",
            "name_a": "name_a_2"
        },
        {
            "__tag__": "ClassB",
            "pid": "pid_b_1",
            "name_b": "name_b_1"
        }
    ]
}

@dataclass
class ClassA:
    pid: str
    name_a: str


@dataclass
class ClassB:
    pid: str
    name_b: str

@dataclass
class Thing:
    pid: str
    multislot: list[Union[ClassA, ClassB]]


x = fromdict(Thing, json_obj_1)
print(x)


x = Thing(**json_obj_1)
print(x)

#x = Thing(**json_obj_2)
#print(x)
#print(dataclass_asdict(x))


x = Thing(
    pid="thing_1",
    multislot=[
        ClassA(pid="a_1", name_a="a_1"),
        ClassB(pid="b_1", name_b="b_1"),
    ]
)
print(x)
print(dataclass_asdict(x))


y = asdict(x)
print(y)

z = fromdict(Thing, json_obj_2)
print(z)
