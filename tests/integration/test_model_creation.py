import datetime
from types import NoneType
from typing import List, Dict, Tuple, Optional, Union

import pytest
from pydantic import PydanticUserError, ValidationError as PydanticValidationError

from pydantic_mongo import PydanticMongoModel as PMM
from pydantic_mongo.extensions import ValidationError


@pytest.mark.parametrize("collection_name", [
    "test_models",
    "tests"
])
def test_creation(mongo, collection_name):
    class TestModel(PMM):
        __collection_name__ = collection_name if collection_name == "tests" else None
        pass

    test_model = TestModel()
    test_model.save()

    assert test_model.id is not None
    assert test_model.collection_name == collection_name
    assert test_model.__mongo__ == mongo
    assert test_model.collection() == mongo.db[collection_name]
    assert test_model._get_type_by_collection(collection_name) == TestModel


def test_creation_with_simple_data(mongo):
    try:
        class _(PMM):
            age = 0
    except Exception as e:
        assert isinstance(e, PydanticUserError)

    class TestModel(PMM):
        age: int

    try:
        TestModel()
    except Exception as e:
        assert isinstance(e, PydanticValidationError)

    test_model = TestModel(age=10)

    assert test_model.age == 10
    assert test_model.id is None

    test_model.save()

    assert test_model.id is not None
    assert test_model.age == 10

    test_model.age = 20
    test_model.save()

    assert test_model.age == 20


def test_creation_with_list_data(mongo):
    class TestModel(PMM):
        ages: list[int]

    test_model = TestModel(ages=[10, 20])

    assert test_model.ages == [10, 20]
    assert test_model.id is None

    test_model.save()

    assert test_model.id is not None
    assert test_model.ages == [10, 20]

    test_model.ages = [20, 30]
    test_model.save()

    assert test_model.ages == [20, 30]


def test_creation_with_dict_data(mongo):
    class TestModel(PMM):
        ages: dict[str, int]

    test_model = TestModel(ages={"a": 10, "b": 20})

    assert test_model.ages == {"a": 10, "b": 20}
    assert test_model.id is None

    test_model.save()

    assert test_model.id is not None
    assert test_model.ages == {"a": 10, "b": 20}

    test_model.ages = {"a": 20, "b": 30}
    test_model.save()

    assert test_model.ages == {"a": 20, "b": 30}


def test_creation_with_nested_data(mongo):
    class TestModel(PMM):
        ages: dict[str, list[int]]

    test_model = TestModel(ages={"a": [10, 20], "b": [30, 40]})

    assert test_model.ages == {"a": [10, 20], "b": [30, 40]}
    assert test_model.id is None

    test_model.save()

    assert test_model.id is not None
    assert test_model.ages == {"a": [10, 20], "b": [30, 40]}

    test_model.ages = {"a": [20, 30], "b": [40, 50]}
    test_model.save()

    assert test_model.ages == {"a": [20, 30], "b": [40, 50]}


def test_creation_with_various_types(mongo):
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
    )
    test_model.save()

    assert test_model.list_ == [1, 2, 3]
    assert test_model.dict_ == {"a": 1, "b": 2}
    assert test_model.tuple_ == (1, "a")
    assert test_model.none_ is None
    assert test_model.optional_ is None
    assert test_model.union_ == 1
    assert isinstance(test_model.date_, datetime.date)
    assert test_model.complex_ == [1, 2, 3]


@pytest.mark.parametrize("attributes, annotations", [
    ({"bytes_": b"123"}, {"bytes_": bytes}),
    ({"set_": {1, 2, 3}}, {"set_": set}),
    ({"frozenset_": frozenset({1, 2, 3})}, {"frozenset_": frozenset}),
    ({"complex_": complex(1, 2)}, {"complex_": complex}),
    ({"callable_": lambda x: x}, {"callable_": callable}),
    ({"generator_": (i for i in range(10))}, {"generator_": type((i for i in range(10)))}),
    ({"ellipsis_": Ellipsis}, {"ellipsis_": type(Ellipsis)}),
    ({"module_": datetime}, {"module_": type(datetime)}),
    ({"any_": ...}, {"any_": type(...)}),
])
def test_creation_with_unsupported_types(mongo, attributes, annotations):
    attributes.update({"__annotations__": annotations})
    try:
        type("TestModel", (PMM,), attributes)
    except Exception as e:
        assert isinstance(e, ValidationError)


def test_creation_with_nested_models(mongo):
    class NestedModel(PMM):
        age: int

    class TestModel(PMM):
        nested_model: NestedModel

    try:
        TestModel(nested_model=NestedModel(age=10))
    except Exception as e:
        assert isinstance(e, ValueError)

    nested_model = NestedModel(age=10).save()
    test_model = TestModel(nested_model=nested_model).save()

    assert test_model.nested_model.age == 10

    test_model.nested_model.age = 20
    test_model.save()

    assert test_model.nested_model.age == 20


def test_creation_with_nested_models_as_list(mongo):
    class NestedModel(PMM):
        age: int

    class TestModel(PMM):
        nested_models: List[NestedModel]

    nested_model = NestedModel(age=10).save()
    nested_model2 = NestedModel(age=20).save()
    test_model = TestModel(nested_models=[nested_model, nested_model2])

    assert test_model.nested_models[0].age == 10
    assert test_model.nested_models[1].age == 20

    test_model.save()

    assert test_model.nested_models[0].age == 10
    assert test_model.nested_models[1].age == 20


def test_creation_with_nested_models_as_dict(mongo):
    class NestedModel(PMM):
        age: int

    class TestModel(PMM):
        nested_models: Dict[str, NestedModel]

    nested_model = NestedModel(age=10).save()
    nested_model2 = NestedModel(age=20).save()
    test_model = TestModel(nested_models={"a": nested_model, "b": nested_model2})

    assert test_model.nested_models["a"].age == 10
    assert test_model.nested_models["b"].age == 20

    test_model.save()

    assert test_model.nested_models["a"].age == 10
    assert test_model.nested_models["b"].age == 20


def test_creation_with_parse_db_refs(mongo):
    class NestedModel(PMM):
        age: int

    class TestModel(PMM):
        nested_model: NestedModel

    nested_model = NestedModel(age=10).save()
    nested_model_data = {"id": nested_model.id, "collection": nested_model.collection_name, "database": ""}
    test_model = TestModel.get_with_parse_db_refs({"nested_model": nested_model_data}).save()

    assert test_model.nested_model.age == 10


def test_creation_with_nested_model_with_parse_db_refs_false(mongo):
    class NestedModel(PMM):
        age: int

    class TestModel(PMM):
        nested_model: NestedModel

    nested_model = NestedModel(age=10).save()
    nested_model_data = {"id": nested_model.id, "collection": nested_model.collection_name, "database": ""}

    with pytest.raises(PydanticValidationError):
        TestModel(nested_model=nested_model_data).save()
