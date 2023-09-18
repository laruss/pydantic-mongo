from typing import Dict, Optional

import pytest
from bson import ObjectId

from pydantic_mongo import PydanticMongoModel as PMM


def test_from_ref(mongo):
    class TestModel(PMM):
        age: int

    test_model = TestModel(age=10).save()
    _id = test_model.id

    test_model = TestModel.from_ref(test_model.db_ref)

    assert test_model.age == 10
    assert test_model.id == _id


def test_get_ref_objects(mongo):
    class ExternalModel(PMM):
        name: str

    class TestModel(PMM):
        name: str
        external_model: ExternalModel
        external_dict: Dict[str, ExternalModel]

    external_model = ExternalModel(name="external").save()
    test_model = TestModel(name="test", external_model=external_model, external_dict={"test": external_model})

    assert test_model.get_ref_objects() is None

    test_model.id = ObjectId()

    assert test_model.get_ref_objects() is None

    test_model.id = None
    test_model.save()

    ref_objects = test_model.get_ref_objects()
    assert len(ref_objects) == 2

    ref_obj1 = ref_objects[0]
    assert ref_obj1.__is_loaded__ is False

    assert ref_obj1.name == "external"
    assert ref_obj1.__is_loaded__

    assert ref_obj1.id == external_model.id

    assert ref_objects[1].name == "external"
    assert ref_objects[1].id == external_model.id


def test_optional_get_ref_objects(mongo):
    class ExternalModel(PMM):
        name: str

    class TestModel(PMM):
        name: str
        external_model: Optional[ExternalModel] = None

    external_model = ExternalModel(name="external").save()

    test_model = TestModel(name="test").save()
    test_model2 = TestModel(name="test2", external_model=external_model).save()

    assert len(test_model.get_ref_objects()) == 0
    assert len(test_model2.get_ref_objects()) == 1


def test_delete(mongo):
    class TestModel(PMM):
        name: str

    test_model = TestModel(name="test").save()

    assert len(list(TestModel.objects())) == 1

    test_model2 = TestModel(name="test2")

    test_model2.delete()

    assert len(list(TestModel.objects())) == 1

    test_model.delete()

    assert len(list(TestModel.objects())) == 0


def test_model_dump(mongo):
    class TestModel(PMM):
        name: str

    test_model = TestModel(name="test").save()

    model_dump = {"name": "test", "id": test_model.id}

    assert test_model.model_dump() == model_dump

    assert test_model.model_dump(as_mongo_model=True) == model_dump


@pytest.mark.parametrize(
    "load_from_db",
    [True, False],
)
def test_model_dump_with_nested_models(mongo, load_from_db):
    class NestedModel(PMM):
        age: int

    class TestModel(PMM):
        name: str
        age: Optional[int]
        nested_model: NestedModel

    nested_model = NestedModel(age=10).save()
    test_model = TestModel(name="test", age=20, nested_model=nested_model).save()

    if load_from_db:
        test_model = TestModel.get_by_id(test_model.id)
        assert test_model.nested_model.__is_loaded__ is False

    assert test_model.model_dump() == {
        'id': test_model.id,
        'name': 'test',
        'age': 20,
        'nested_model': {
            'id': nested_model.id,
            'age': 10
        }
    }

    assert test_model.model_dump(as_mongo_model=True) == {
        'id': test_model.id,
        'name': 'test',
        'age': 20,
        'nested_model': {
            'collection': 'nested_models',
            'database': "",
            'id': nested_model.id,
        }
    }


def test_model_dump_with_nested_models_deleted(mongo):
    class NestedModel(PMM):
        age: int

    class TestModel(PMM):
        name: str
        age: Optional[int]
        nested_model: NestedModel

    nested_model = NestedModel(age=10).save()
    test_model = TestModel(name="test", age=20, nested_model=nested_model).save()
    nested_model.delete()

    test_model = TestModel.get_by_id(test_model.id)
    _ = test_model.nested_model

    assert test_model.model_dump() == {
        'id': test_model.id,
        'name': 'test',
        'age': 20,
        'nested_model': {'age': None, 'id': None}
    }


def test_model_json_schema(mongo):
    class TestModel(PMM):
        name: str

    schema = TestModel.model_json_schema()
    properties = schema.get("properties")
    assert properties.get("name") == {"title": "Name", "type": "string"}
    assert properties.get("id") == {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'default': None, 'title': 'Id'}

    mm_schema = TestModel.model_json_schema(as_mongo_model=True)
    mm_properties = mm_schema.get("properties")
    assert mm_properties.get("name") == {"title": "Name", "type": "string"}
    assert mm_properties.get("id") == {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'title': 'Id'}


def test_model_json_schema_with_nested_objects(mongo):
    class NestedModel(PMM):
        age: int

    class TestModel(PMM):
        name: str
        age: Optional[int]
        nested_model: NestedModel

    schema = TestModel.model_json_schema()
    properties = schema.get("properties")
    assert isinstance(properties.get("nested_model").get("$ref"), str)

    mm_schema = TestModel.model_json_schema(as_mongo_model=True)
    mm_properties = mm_schema.get("properties")
    assert isinstance(mm_properties.get("nested_model").get("$ref"), str)
