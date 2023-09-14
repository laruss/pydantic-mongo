import datetime
from types import NoneType
from typing import List, Dict, Tuple, Optional, Union

from bson import ObjectId

from pydantic_mongo import PydanticMongoModel as PMM


def test_loading(mongo):
    class TestModel(PMM):
        age: int

    test_model = TestModel(age=10).save()
    _id = test_model.id

    test_model = TestModel.get_by_id(_id)

    assert test_model.age == 10
    assert test_model.id == _id


def test_loading_not_found(mongo):
    class TestModel(PMM):
        age: int

    object_id = ObjectId()
    test_model = TestModel.get_by_id(str(object_id))

    assert test_model is None


def test_loading_with_various_types(mongo):
    class TestModel(PMM):
        list_: List[int]
        dict_: Dict[str, int]
        tuple_: Tuple[int, str]
        none_: NoneType
        optional_: Optional[int]
        union_: Union[int, str]
        date_: datetime.date
        complex_: Union[datetime.date, List[int], Dict[str, int], Tuple[int, str], None]

    test_model = TestModel(
        list_=[1, 2, 3],
        dict_={"a": 1, "b": 2},
        tuple_=(1, "a"),
        none_=None,
        optional_=None,
        union_=1,
        date_=datetime.datetime(2023, 1, 1),
        complex_=[1, 2, 3],
    ).save()

    _id = test_model.id

    test_model = TestModel.get_by_id(_id)

    assert test_model.list_ == [1, 2, 3]
    assert test_model.dict_ == {"a": 1, "b": 2}
    assert test_model.tuple_ == (1, "a")
    assert test_model.none_ is None
    assert test_model.optional_ is None
    assert test_model.union_ == 1
    assert isinstance(test_model.date_, datetime.date)
    assert test_model.complex_ == [1, 2, 3]


def test_loading_with_nested_models(mongo):
    class NestedModel(PMM):
        age: int

    class TestModel(PMM):
        nested_model: NestedModel

    nested_model = NestedModel(age=10).save()
    nested_model_id = nested_model.id
    test_model = TestModel(nested_model=nested_model).save()

    test_model = TestModel.get_by_id(test_model.id)
    nested_model = test_model.nested_model

    assert nested_model.__is_loaded__ is False
    assert nested_model.age == 10
    assert nested_model.__is_loaded__ is True
    assert nested_model.id == nested_model_id


def test_loading_with_nested_models_list(mongo):
    class NestedModel(PMM):
        age: int

    class TestModel(PMM):
        nested_models: List[NestedModel]

    nested_model = NestedModel(age=10).save()
    nested_model2 = NestedModel(age=20).save()
    nested_model_id = nested_model.id
    nested_model2_id = nested_model2.id
    test_model = TestModel(nested_models=[nested_model, nested_model2]).save()

    test_model = TestModel.get_by_id(test_model.id)
    nested_model = test_model.nested_models[0]
    nested_model2 = test_model.nested_models[1]

    assert nested_model.age == 10
    assert nested_model2.age == 20
    assert test_model.nested_models[0].id == nested_model_id
    assert test_model.nested_models[1].id == nested_model2_id


def test_loading_with_nested_models_dict(mongo):
    class NestedModel(PMM):
        age: int

    class TestModel(PMM):
        nested_models_dict: Dict[str, NestedModel]

    nested_model = NestedModel(age=10).save()
    nested_model2 = NestedModel(age=20).save()
    nested_model_id = nested_model.id
    nested_model2_id = nested_model2.id
    test_model = TestModel(nested_models_dict={"a": nested_model, "b": nested_model2}).save()

    test_model = TestModel.get_by_id(test_model.id)
    nested_model = test_model.nested_models_dict["a"]
    nested_model2 = test_model.nested_models_dict["b"]

    assert nested_model.age == 10
    assert nested_model2.age == 20
    assert test_model.nested_models_dict["a"].id == nested_model_id
    assert test_model.nested_models_dict["b"].id == nested_model2_id


def test_loading_nested_models_complex_structure(mongo):
    class NestedModel(PMM):
        age: int

    class TestModel(PMM):
        nested_models: List[NestedModel]
        nested_models_dict: Dict[str, NestedModel]
        nested_model: NestedModel

    nested_model = NestedModel(age=10).save()
    nested_model2 = NestedModel(age=20).save()
    nested_model_id = nested_model.id
    nested_model2_id = nested_model2.id
    test_model = TestModel(
        nested_models=[nested_model, nested_model2],
        nested_models_dict={"a": nested_model, "b": nested_model2},
        nested_model=nested_model
    ).save()

    test_model = TestModel.get_by_id(test_model.id)
    nested_model = test_model.nested_models[0]
    nested_model2 = test_model.nested_models[1]
    nested_model_dict = test_model.nested_models_dict["a"]
    nested_model2_dict = test_model.nested_models_dict["b"]
    nested_model3 = test_model.nested_model

    assert nested_model.age == 10
    assert nested_model2.age == 20
    assert nested_model_dict.age == 10
    assert nested_model2_dict.age == 20
    assert nested_model3.age == 10
    assert test_model.nested_models[0].id == nested_model_id
    assert test_model.nested_models[1].id == nested_model2_id
    assert test_model.nested_models_dict["a"].id == nested_model_id
    assert test_model.nested_models_dict["b"].id == nested_model2_id


def test_loading_all_objects(mongo):
    class TestModel(PMM):
        age: int

    TestModel(age=10).save()
    TestModel(age=20).save()
    TestModel(age=30).save()

    test_models = list(TestModel.objects())

    assert len(list(test_models)) == 3
    assert test_models[0].age == 10
    assert test_models[1].age == 20
    assert test_models[2].age == 30


def test_loading_all_objects_by_filter(mongo):
    class TestModel(PMM):
        age: int

    TestModel(age=10).save()
    TestModel(age=20).save()
    TestModel(age=30).save()

    test_models = list(TestModel.objects({"age": 20}))

    assert len(list(test_models)) == 1
    assert test_models[0].age == 20
