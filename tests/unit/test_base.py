from __future__ import annotations

from unittest import mock
from unittest.mock import patch

from pymongo import IndexModel
from pymongo.errors import PyMongoError

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

    def test_no_indexes_created_when_mongo_config_is_none(self):
        with patch('pydantic_mongo.base.PydanticMongo') as mock_pydanticmongo:
            mock_pydanticmongo.return_value.db.__getitem__.return_value.list_indexes.return_value = []
            Base._init_indexes()
            mock_pydanticmongo.return_value.db.__getitem__.assert_not_called()
            mock_pydanticmongo.return_value.db.__getitem__.return_value.list_indexes.assert_not_called()
            mock_pydanticmongo.return_value.db.__getitem__.return_value.create_indexes.assert_not_called()

    def test_no_indexes_created_when_cls_indexes_is_none(self):
        with patch('pydantic_mongo.base.PydanticMongo') as mock_pydanticmongo:
            mock_pydanticmongo.return_value.db.__getitem__.return_value.list_indexes.return_value = []
            Base._MongoConfig = mock.Mock()
            Base._MongoConfig.indexes = None
            Base._init_indexes()
            mock_pydanticmongo.return_value.db.__getitem__.assert_not_called()
            mock_pydanticmongo.return_value.db.__getitem__.return_value.list_indexes.assert_not_called()
            mock_pydanticmongo.return_value.db.__getitem__.return_value.create_indexes.assert_not_called()

    def test_no_indexes_created_when_cls_indexes_is_empty_list(self):
        with patch('pydantic_mongo.base.PydanticMongo') as mock_pydanticmongo:
            mock_pydanticmongo.return_value.db.__getitem__.return_value.list_indexes.return_value = []
            Base._MongoConfig = mock.Mock()
            Base._MongoConfig.indexes = []
            Base._init_indexes()
            mock_pydanticmongo.return_value.db.__getitem__.assert_not_called()
            mock_pydanticmongo.return_value.db.__getitem__.return_value.list_indexes.assert_not_called()
            mock_pydanticmongo.return_value.db.__getitem__.return_value.create_indexes.assert_not_called()

    def test_type_error_raised_when_cls_indexes_is_not_list(self):
        with patch('pydantic_mongo.base.PydanticMongo') as mock_pydanticmongo, \
                patch('pydantic_mongo.base.__Base._MongoConfig') as mock_mongo_config:
            mock_pydanticmongo.return_value.db.__getitem__.return_value.list_indexes.return_value = []
            mock_mongo_config.indexes = "test"
            with self.assertRaises(TypeError):
                Base._init_indexes()
            mock_pydanticmongo.return_value.db.__getitem__.assert_not_called()
            mock_pydanticmongo.return_value.db.__getitem__.return_value.list_indexes.assert_not_called()
            mock_pydanticmongo.return_value.db.__getitem__.return_value.create_indexes.assert_not_called()

    def test_type_error_raised_when_cls_indexes_contains_non_index_model_objects(self):
        with patch('pydantic_mongo.base.PydanticMongo') as mock_pydanticmongo, \
                patch('pydantic_mongo.base.__Base._MongoConfig') as mock_mongo_config:
            mock_pydanticmongo.return_value.db.__getitem__.return_value.list_indexes.return_value = []
            print(f"{Base=}")
            mock_mongo_config.indexes = [mock.Mock()]
            with self.assertRaises(TypeError):
                Base._init_indexes()
            mock_pydanticmongo.return_value.db.__getitem__.assert_called_once_with("__bases")
            mock_pydanticmongo.return_value.db.__getitem__.return_value.list_indexes.assert_called_once()
            mock_pydanticmongo.return_value.db.__getitem__.return_value.create_indexes.assert_not_called()

    def test_pymongo_error_raised_when_creating_indexes_fails(self):
        with patch('pydantic_mongo.base.PydanticMongo') as mock_pydanticmongo, \
                patch('pydantic_mongo.base.__Base._MongoConfig') as mock_mongo_config:
            gi = mock_pydanticmongo.return_value.db.__getitem__
            gi.return_value.list_indexes.return_value = []
            index_model = IndexModel([("test", 1)])
            mock_mongo_config.indexes = [index_model]
            gi.return_value.create_indexes = mock.Mock(side_effect=PyMongoError)
            with self.assertRaises(PyMongoError):
                Base._init_indexes()
            gi.assert_called_once_with(Base.collection_name)
            gi.return_value.list_indexes.assert_called_once()
            gi.return_value.create_indexes.assert_called_once_with([index_model])

    def test_forbidden_fields(self):
        bm = Base()
        with self.assertRaises(ValueError):
            bm.new_field = "test"

    def test__mongo__(self):
        self.assertEqual(Base.__mongo__, PydanticMongo())

    def test_pydantic_mongo_db_exists_but_init_indexes_does_not_create_indexes(self):
        with patch('pydantic_mongo.base.PydanticMongo') as mock_pydanticmongo, \
                patch('pydantic_mongo.base.__Base._init_indexes') as mock_init_indexes:
            engine = mock_pydanticmongo.return_value
            engine.db = mock.Mock()
            Base.__mongo__
            mock_pydanticmongo.assert_called_once_with()
            self.assertEqual(engine.db, Base.__mongo__.db)
            mock_init_indexes.assert_called()

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
