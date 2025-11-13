from pathlib import Path

from dacite import (
    Config,
    from_dict,
)
from linkml.generators.pythongen import PythonGenerator
from linkml.utils.datautils import (
    get_dumper,
    get_loader,
)
from linkml_runtime import SchemaView

from ..generators.dump_things_pythongen import DumpThingsPythonGenerator


schema_file = Path(__file__).parent / "testschema.yaml"


json_objects = [
    {
        'pid': 'pid_x',
        'given_name': 'p_x',
        'multislot_list': [
            {
                'fruit_id': 'banana_1',
                'color': 'yellow',
            },
            {
                'fruit_id': 'banana_2',
                'color': 'brown',
            },
            {
                'car_id': 'car_1',
                'wheels': 4,
            },
        ],
    },
    {
        'pid': 'pid_x',
        'given_name': 'p_x',
        'multislot_dict': {
            'banana_1': {
                'fruit_id': 'banana_1',
                'color': 'yellow',
            },
            'banana_2': {
                'fruit_id': 'banana_2',
                'color': 'brown',
            },
            'car_1': {
                'car_id': 'car_1',
                'wheels': 4,
            },
        },
    },
    {
        'pid': 'pid_x',
        'given_name': 'p_x',
        'multislot_dict': {
            'banana_1': 'yellow',
            'banana_2': 'brown',
            'car_1': 4,
        },
    },
    {
        'pid': 'pid_x',
        'given_name': 'p_x',
        'multislot_dict': {
            'banana_1': {
                'color': 'yellow',
            },
            'banana_2': {
                'color': 'brown',
            },
            'car_1': {
                'wheels': 4,
            },
        },
    },
]

should_pass_old = (0, 1, 2, 3)
should_pass_new = (0, 1)

schema_view = SchemaView(schema_file)

new_model = DumpThingsPythonGenerator(schema_file).compile_module()
old_model = PythonGenerator(schema_file).compile_module()


def test_old_basic():
    loader = get_loader('json')
    for index, json_object in enumerate(json_objects):
        data_obj = loader.load(
            source=json_object,
            target_class=old_model.Person,
        )
        print('LinkML loader:', data_obj)
        data_obj = from_dict(
            old_model.Person,
            json_object,
            Config(strict=True, strict_unions_match=False),
        )
        print('dacite loader:', data_obj)
        print('----------------')


def test_new_basic():
    loader = get_loader('json')
    for index, json_object in enumerate(json_objects):
        print('Input:', json_object)
        data_obj = loader.load(
            source=json_object,
            target_class=new_model.Person,
        )
        print('LinkML loader:', data_obj)
        if index not in should_pass_new:
            continue
        data_obj = from_dict(
            new_model.Person,
            json_object,
            Config(strict=True, strict_unions_match=True),
        )
        print('dacite loader:', data_obj)
        print('----------------')
