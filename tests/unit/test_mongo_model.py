from __future__ import annotations

import datetime
from typing import Optional, Dict, Union, Callable

from bson import DBRef
from pydantic import BaseModel, Field

from pydantic_mongo.base import __Base as Base
from pydantic_mongo.db_ref_model import DbRefModel
from pydantic_mongo.mongo_model import MongoModel
from tests.unit.base import BaseTest


class TestMongoModel(BaseTest):
    def test_mongo_model_init(self):
        mm = MongoModel()
        self.assertIsNone(mm.id)

    def test_model_dump(self):
        mm = MongoModel()
        self.assertEqual(mm.model_dump(), {"_id": None})

        mm = MongoModel(id="123")
        self.assertEqual(mm.model_dump(), {"_id": "123"})
        self.assertEqual(mm.model_dump(exclude={"id"}), {})

    def test_is_complex_type(self):
        mm = MongoModel()
        for item in [str, int, float, bool, dict, list, tuple, set]:
            self.assertFalse(mm._is_complex_type(item))

        for item in [Optional[str], Dict[str, int], list[str], tuple[str], set[str], Union[str, None]]:
            self.assertTrue(mm._is_complex_type(item))

    def test_get_fields_from_annotation(self):
        MM = MongoModel

        class TestModel(BaseModel):
            id: Optional[str] = Field(alias="_id", default=None)
            name: str
            age: int
            is_active: bool
            data: dict[str, int]
            list_data: list[str]
            ref: Optional[MM]

        fields = MM._get_fields_from_annotation("test", TestModel.model_fields["name"].annotation, MM)
        self.assertEqual(fields, {"test": (str, ...)})

        fields = MM._get_fields_from_annotation("test", TestModel.model_fields["age"].annotation, MM)
        self.assertEqual(fields, {"test": (int, ...)})

        fields = MM._get_fields_from_annotation("test", TestModel.model_fields["is_active"].annotation, MM)
        self.assertEqual(fields, {"test": (bool, ...)})

        fields = MM._get_fields_from_annotation("test", TestModel.model_fields["data"].annotation, MM)
        self.assertEqual(fields, {"test": (dict[str, int], ...)})

        fields = MM._get_fields_from_annotation("test", TestModel.model_fields["list_data"].annotation, MM)
        self.assertEqual(fields, {"test": (list[str], ...)})

        fields = MM._get_fields_from_annotation("test", TestModel.model_fields["ref"].annotation, DbRefModel)
        self.assertEqual({"test": (Optional[MM], ...)}, fields)

    def test_get_fields_validators_from_annotation(self):
        MM = MongoModel

        class TestModel(Base):
            name: str
            age: int
            is_active: bool
            data: dict[str, int]
            list_data: list[str]
            child: Optional[TestModel] = None

        test_obj = TestModel(name="test", age=10, is_active=True, data={"a": 1}, list_data=["a", "b"])
        test_obj2 = TestModel(name="test2", age=20, is_active=False, data={"a": 2}, list_data=["c", "d"])
        test_obj2.child = test_obj

        fields = MM._get_fields_validators_from_annotation(TestModel.model_fields["name"].annotation, DbRefModel)
        self.assertIsNone(fields)

        fields = MM._get_fields_validators_from_annotation(TestModel.model_fields["age"].annotation, DbRefModel)
        self.assertIsNone(fields)

        fields = MM._get_fields_validators_from_annotation(TestModel.model_fields["is_active"].annotation, DbRefModel)
        self.assertIsNone(fields)

        fields = MM._get_fields_validators_from_annotation(TestModel.model_fields["data"].annotation, DbRefModel)
        self.assertTrue(isinstance(fields, Callable))
        self.assertEqual(fields({"a": 1}), {"a": 1})
        self.assertEqual(
            fields({"a": test_obj}), {'a': DbRefModel(collection='test_models', id=None, database=None)})

        fields = MM._get_fields_validators_from_annotation(TestModel.model_fields["list_data"].annotation, DbRefModel)
        self.assertTrue(isinstance(fields, Callable))
        self.assertEqual(fields(["a", "b"]), ["a", "b"])
        self.assertEqual(
            fields([test_obj]), [DbRefModel(collection='test_models', id=None, database=None)])

        fields = MM._get_fields_validators_from_annotation(TestModel.model_fields["child"].annotation, DbRefModel)
        self.assertTrue(isinstance(fields, Callable))
        self.assertEqual(fields(test_obj), DbRefModel(collection='test_models', id=None, database=None))

    def test_convert_to_db_ref_if_needed(self):
        mm = MongoModel()
        db_ref_obj = DbRefModel(collection="test", id="123", database="test_db")

        self.assertEqual(mm._convert_to_db_ref_if_needed({"_id": "123"}), {"_id": "123"})
        self.assertEqual(mm._convert_to_db_ref_if_needed({"_id": "123", "name": "test"}), {"_id": "123", "name": "test"})
        self.assertEqual(mm._convert_to_db_ref_if_needed(db_ref_obj.model_dump()), DBRef('test', '123', 'test_db'))
        self.assertEqual(
            mm._convert_to_db_ref_if_needed({"child": db_ref_obj.model_dump()}),
            {"child": DBRef('test', '123', 'test_db')}
        )
        self.assertEqual(
            mm._convert_to_db_ref_if_needed({"child": [db_ref_obj.model_dump()]}),
            {"child": [DBRef('test', '123', 'test_db')]}
        )

    def test_model_dump_db(self):
        class MM(MongoModel):
            someObj: Optional[DbRefModel] = None
            date_field: Optional[datetime.datetime] = None

        db_ref_obj = DbRefModel(collection="test", id="123", database="test_db")
        mm = MM(someObj=db_ref_obj, date_field=datetime.datetime(2022, 1, 1, 12, 0))

        self.assertEqual(MongoModel().model_dump_db(), {})
        self.assertEqual(mm.model_dump_db(),
                         {"someObj": DBRef('test', '123', 'test_db'), "date_field": "2022-01-01T12:00:00"})
        self.assertEqual(
            mm.model_dump_db(convert_to_db=False),
            {'id': None, 'someObj': {'collection': 'test', 'id': '123', 'database': 'test_db'},
             'date_field': '2022-01-01T12:00:00'}
        )

    def test_from_model(self):
        class TestModel(Base):
            name: str
            age: int
            is_active: bool
            data: dict[str, int]
            list_data: list[str]
            child: Optional[TestModel] = None

        MM = MongoModel.from_model(TestModel)
        self.assertEqual(MM.__name__, "MongoModel")
        self.assertEqual(MM.__base__, MongoModel)
        ans = MM.__annotations__
        child_type = "typing.Optional[pydantic.main.DbRefModel]"

        self.assertEqual(f"{ans['child']}", child_type)

        del ans["child"]
        self.assertEqual(ans, {
            "id": Optional[str],
            "name": str,
            "age": int,
            "is_active": bool,
            "data": dict[str, int],
            "list_data": list[str]
        })
        self.assertTrue(issubclass(MM, MongoModel))
