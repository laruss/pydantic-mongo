from __future__ import annotations

from pydantic_mongo import PydanticMongo
from pydantic_mongo.base import __Base as Base
from tests.unit.base import BaseTest


class TestBaseModel(BaseTest):
    def test_base_model_init(self):
        bm = Base()
        self.assertIsNone(bm.id)

    def test_collection_name(self):
        bm = Base()
        self.assertEqual(bm.collection_name, "__bases")
        self.assertEqual(Base.collection_name, "__bases")

        class Test(Base):
            __collection_name__ = "test"

        self.assertEqual(Test.collection_name, "test")

        class SuperTest(Base):
            pass

        self.assertEqual(SuperTest.collection_name, "super_tests")

    def test_forbidden_fields(self):
        bm = Base()
        with self.assertRaises(ValueError):
            bm.new_field = "test"

    def test__mongo__(self):
        self.assertEqual(Base.__mongo__, PydanticMongo())

    def test_collection(self):
        with self.assertRaises(ValueError):
            Base.collection()

        PydanticMongo().init_app(self.app)
        self.assertEqual(Base.collection(), PydanticMongo().db["__bases"])

    def test_get_type_by_collection(self):
        with self.assertRaises(ValueError):
            Base._get_type_by_collection("test_000123")

        class Test(Base):
            pass

        self.assertEqual(Test._get_type_by_collection("tests"), Test)
