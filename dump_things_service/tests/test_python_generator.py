from pathlib import Path

from dacite import (
    Config,
    from_dict,
)
from linkml.generators.pythongen import PythonGenerator as PythonGeneratorOld
from linkml.utils.datautils import (
    get_dumper,
    get_loader,
)
from linkml_runtime import SchemaView

from ..generators.pythongen import PythonGenerator as PythonGeneratorNew


schema_file = Path(__file__).parent / "testschema.yaml"


json_objects = [
    {
        'pid': 'pid_x',
        'given_name': 'p_x',
        'multislot': [
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
        'multislot': {
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
        'multislot': {
            'banana_1': 'yellow',
            'banana_2': 'brown',
            'car_1': 4,
        },
    },
    {
        'pid': 'pid_x',
        'given_name': 'p_x',
        'multislot': {
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

list_object = 0
dict_object = 1
simple_dict_object = 2
reducted_dict_object = 3

schema_view = SchemaView(schema_file)

new_model = PythonGeneratorNew(schema_file).compile_module()
old_model = PythonGeneratorOld(schema_file).compile_module()


def test_old_basic():

    loader = get_loader('json')
    for index, json_object in enumerate(json_objects):
        data_obj = loader.load(
            source=json_object,
            target_class=old_model.Person,
        )
        print('LinkML loader:', data_obj)
        if index == simple_dict_object:
            continue
        data_obj = from_dict(
            old_model.Person,
            json_object,
            Config(strict=True, strict_unions_match=False),
        )
        print('dacite loader:', data_obj)


def test_new_basic():
    loader = get_loader('json')
    for index, json_object in enumerate(json_objects):
        print('Input:', json_object)
        data_obj = loader.load(
            source=json_object,
            target_class=new_model.Person,
        )
        print('LinkML loader:', data_obj)
        if index in (simple_dict_object, reducted_dict_object):
            continue
        data_obj = from_dict(
            new_model.Person,
            json_object,
            Config(strict=True, strict_unions_match=True),
        )
        print('dacite loader:', data_obj)
        print('----------------')

x = """
@pytest.mark.parametrize('model', [old_model, new_model])
@pytest.mark.parametrize('json_object_index', [0, 1, 2])
def test_basic(model, json_object_index):

    #if model == new_model and json_object_index == 2:
    #    raise pytest.skip('simplified ')

    loader = get_loader('json')
    data_obj = loader.load(
        source=json_objects[json_object_index],
        target_class=model.Person,
    )
    print('LinkML loader:', data_obj)
    data_obj = from_dict(
        old_model.Person,
        json_objects[json_object_index],
        Config(strict=True, strict_unions_match=False),
    )
    print('dacite loader:', data_obj)
"""


x = """
typing.Union[
    dict[test.ThingPid, typing.Union[test.Annotation, test.Bemerkung]],
    list[typing.Union[test.Annotation, test.Bemerkung]],
    NoneType
]
"""
