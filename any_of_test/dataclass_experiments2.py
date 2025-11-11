from __future__ import annotations

import sys

from linkml_runtime.utils.schemaview import SchemaView
from dacite import from_dict, Config

from dump_things_service.model import get_schema_model_for_schema

schema = 'schema2.yaml'


model = get_schema_model_for_schema(schema)
sv = SchemaView(schema)

Thing = model.Thing


json_obj_1 = {
    "pid": "thing_1",
    "annotations": [],
}

json_obj_2 = {
    "pid": "thing_2",
    "annotations": [
        {
            "annotation_tag": "pid_1",
            "annotation_value": "v_1",
        },
        {
            "annotation_tag": "pid_2",
            "annotation_value": "v_2"
        },
        {
            "bemerkung_id": "pid_3",
            "bemerkung_inhalt": "v_3",
        },
    ],
}

from linkml.utils.datautils import (
    get_dumper,
    get_loader,
)

loader = get_loader('json')
data_obj_0 = loader.load(
    source=json_obj_2,
    target_class=Thing,
    schemaview=sv,
)
print(data_obj_0)


data_obj = from_dict(
    Thing,
    json_obj_2,
    Config(strict=True, strict_unions_match=True),
)

print(data_obj)

dumper = get_dumper('json')
ttl_object = dumper.dumps(data_obj)
print(ttl_object)

sys.exit(0)

dumper = get_dumper('ttl')
ttl_object = dumper.dumps(data_obj, schemaview=sv)
print(ttl_object)
