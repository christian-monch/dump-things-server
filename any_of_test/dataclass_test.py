from __future__ import annotations

from schema_python_new import Thing

from linkml_runtime.utils.schemaview import SchemaView
from dacite import from_dict, Config


sv = SchemaView('schema.yaml')




json_obj_1 = {
    "pid": "thing_1",
    "multislot": [],
}

json_obj_2 = {
    "pid": "thing_2",
    "multislot": [
        {
            "pid": "pid_a_1",
            "name_a": "name_a_1"
        },
        {
            "pid": "pid_a_2",
            "name_a": "name_a_2"
        },
        {
            "pid": "pid_b_1",
            "name_b": "name_b_1"
        }
    ]
}

from linkml.utils.datautils import (
    get_dumper,
    get_loader,
)

loader = get_loader('json')

data_obj = from_dict(
    Thing,
    json_obj_2,
    Config(strict=True, strict_unions_match=True),
)

print(data_obj)

dumper = get_dumper('ttl')
ttl_object = dumper.dumps(data_obj, schemaview=sv)
print(ttl_object)
