import unittest

from unittest.mock import MagicMock, patch

from bson import DBRef, ObjectId
from bson.errors import InvalidId
from pydantic import ValidationError as PydanticValidationError

from pydantic_mongo.base_pm_model import BasePydanticMongoModel
from tests.unit.base import BaseTest


class TestBasePydanticMongoModel(BaseTest):
    def test_init(self):
        with patch("pydantic_mongo.base_pm_model.MongoModel") as MockedMongoModel:
            MockedMongoModel.from_model.return_value = "test"

            model = BasePydanticMongoModel()

            self.assertIsNotNone(model._MongoModel)
            MockedMongoModel.from_model.assert_called_once_with(BasePydanticMongoModel)
            self.assertEqual(model._MongoModel, "test")

    def test_get_attribute(self):
        class TestModel(BasePydanticMongoModel):
            @classmethod
            def cls_method(cls):
                pass

            def method(self):
                pass

            @property
            def prop(self):
                return "test"

        model = TestModel()

        with patch.object(TestModel, "_load_from_db", MagicMock()) as mocked_method:
            model.__is_loaded__ = False

            self.assertFalse(mocked_method.called)

            model.cls_method()
            self.assertFalse(mocked_method.called)

            model.method()
            self.assertFalse(mocked_method.called)

            _ = model.prop
            self.assertFalse(mocked_method.called)

            _ = model.id
            self.assertTrue(mocked_method.called)

    def test_db_ref(self):
        model = BasePydanticMongoModel()

        with patch.object(model, "__db_ref__", MagicMock()) as mocked_db_ref:
            self.assertTrue(model.db_ref == mocked_db_ref)

        model.__db_ref__ = None
        with self.assertRaises(ValueError):
            _ = model.db_ref

        model.id = "test"

        self.assertTrue(isinstance(model.db_ref, DBRef))
        self.assertEqual(model.db_ref.id, "test")
        self.assertEqual(model.db_ref.collection, model.collection_name)

    def test_parse_db_refs(self):
        with patch(
                "pydantic_mongo.base_pm_model.find_data_with_fields_in_data_and_replace",
                return_value={"_id": "True"}) as mocked_method:
            model = BasePydanticMongoModel()
            model._parse_db_refs({"test": "test"})
            self.assertEqual(({"test": "test"},), mocked_method.call_args[0])

    def test_load_from_db(self):
        with patch.object(BasePydanticMongoModel, '_get_by_filter', return_value=None):
            model = BasePydanticMongoModel()

            with self.assertRaises(ValueError):
                model._load_from_db("test")

        class TestModel(BasePydanticMongoModel):
            name: str

        model = TestModel(name="name")
        model.id = "test"

        with patch.object(TestModel, '_get_by_filter', return_value={"_id": "test_id", "name": "test"}):
            self.assertEqual(model._load_from_db("name"), "test")
            self.assertEqual(model.name, "test")
            self.assertEqual(model.id, "test_id")
            self.assertEqual(model.__is_loaded__, True)

        with patch.object(TestModel, '_get_by_filter', return_value={"_id": "test_id"}):
            model.__db_ref__ = DBRef("test", "test_id")
            self.assertEqual(model._load_from_db("id"), "test_id")
            self.assertEqual(model.id, "test_id")
            with self.assertRaises(AttributeError):
                _ = model.name
            self.assertEqual(model.__is_loaded__, True)

        model = TestModel(name="name")
        model.id = "test"

        with patch.object(TestModel, '_get_by_filter', return_value={"_id": "test_id"}):
            with self.assertRaises(AttributeError):
                model._load_from_db("name")

    def test_save(self):
        class MockCollection(MagicMock):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.inserted_id = "test_id"

            def insert_one(self, *args, **kwargs):
                self.insert_one_called = True
                return self

            def update_one(self, *args, **kwargs):
                self.update_one_called = True
                return self

        mock_collection = MockCollection()

        with patch.object(BasePydanticMongoModel, 'collection', new_callable=lambda: mock_collection):
            model = BasePydanticMongoModel()
            model_dump_db = MagicMock(return_value="test")
            model._MongoModel = MagicMock(model_dump_db=model_dump_db)

            self.assertEqual(model._save(), model)
            self.assertEqual("test_id", model.id)
            self.assertTrue(mock_collection.insert_one_called)

            mock_collection.insert_one_called = False  # Reset flag

            model.id = str(ObjectId())

            self.assertEqual(model._save(), model)
            self.assertTrue(mock_collection.update_one_called)

    def test_from_ref(self):
        class TestModel(BasePydanticMongoModel):
            name: str

        ref = DBRef("test", str(ObjectId()))
        model = TestModel._from_ref(ref)

        self.assertEqual(ref, model.__db_ref__)
        self.assertFalse(model.__is_loaded__)
        with self.assertRaises(ValueError):
            _ = model.name

        with patch.object(TestModel, '_get_by_filter', return_value={"_id": ref.id, "name": "test"}):
            model = TestModel._from_ref(ref, False)
            self.assertEqual(model, {"_id": ref.id, "name": "test"})
            TestModel._get_by_filter.assert_called_with({"_id": ref.id})

        with patch.object(TestModel, '_get_by_filter', return_value=None):
            with self.assertRaises(ValueError):
                TestModel._from_ref(ref, False)

    def test_objects(self):
        find_was_called = False
        find_params = None

        class CollectionMock:
            @staticmethod
            def find(*args, **kwargs):
                nonlocal find_was_called, find_params
                find_params = args
                find_was_called = True
                return ["test1", "test2"]

        with patch.object(
                BasePydanticMongoModel,
                'collection',
                new_callable=MagicMock,
                return_value=CollectionMock()
        ), patch.object(BasePydanticMongoModel, '_process_mongo_doc', return_value="test") as mock_process:
            self.assertEqual(list(BasePydanticMongoModel._objects()), ["test", "test"])
            self.assertTrue(find_was_called)
            self.assertEqual(({},), find_params)
            mock_process.assert_called()
            mock_process.assert_called_with("test2")

            with self.assertRaises(InvalidId):
                list(BasePydanticMongoModel._objects({"_id": "test"}))

            obj_id = ObjectId()
            list(BasePydanticMongoModel._objects({"_id": obj_id}))
            self.assertEqual(({"_id": obj_id},), find_params)

    def test_get_by_filter(self):
        find_one_params = None

        class CollectionMock(MagicMock):
            def find_one(self, *args, **kwargs):
                nonlocal find_one_params
                find_one_params = args
                return "test_result"

        with patch.object(BasePydanticMongoModel, 'collection', new=CollectionMock()) as mock_collection, \
                patch.object(BasePydanticMongoModel, '_process_mongo_doc',
                             return_value="test_mongo_doc") as mock_process_doc:
            # Check initial find_one call
            self.assertEqual(BasePydanticMongoModel._get_by_filter({}), "test_mongo_doc")
            self.assertEqual(({},), find_one_params)
            mock_process_doc.assert_called_once_with('test_result', as_dict=False)

            # Check raising of InvalidId
            with self.assertRaises(InvalidId):
                BasePydanticMongoModel._get_by_filter({"_id": "test"})

            # Check with valid ObjectId
            obj_id = ObjectId()
            BasePydanticMongoModel._get_by_filter({"_id": obj_id}, as_dict=True)
            self.assertEqual(({"_id": obj_id},), find_one_params)
            mock_process_doc.assert_called_with('test_result', as_dict=True)

    @patch("pydantic_mongo.helpers.get_refs_from_data")
    def test_get_ref_objects(self, get_refs_from_data_mock):
        type_by_collection_mock = MagicMock(return_value=MagicMock(_from_ref=MagicMock()))
        BasePydanticMongoModel._get_type_by_collection = type_by_collection_mock
        db_ref = DBRef("test", "test_id")
        get_refs_from_data_mock.return_value = [db_ref]

        model = BasePydanticMongoModel()
        result = model._get_ref_objects({"test": "test"})
        self.assertEqual(result, [type_by_collection_mock.return_value._from_ref.return_value])
        type_by_collection_mock.assert_called_with("test")
        type_by_collection_mock.return_value._from_ref.assert_called_with(db_ref)
        get_refs_from_data_mock.assert_called_with('test')

    def test_replace_refs_with_models(self):
        BPM = BasePydanticMongoModel
        _from_ref_mock = MagicMock()
        BPM._get_type_by_collection = MagicMock(return_value=MagicMock(_from_ref=_from_ref_mock))
        # 1. simple mongo dict without refs
        result = BPM._replace_refs_with_models({"test": "test"})
        self.assertEqual(result, {"test": "test"})
        BPM._get_type_by_collection.assert_not_called()
        # 2. mongo dict with ref
        db_ref = DBRef("test", "test_id")
        result = BPM._replace_refs_with_models({"test": db_ref})
        self.assertEqual({"test": _from_ref_mock.return_value}, result)
        BPM._get_type_by_collection.assert_called_with(db_ref.collection)
        _from_ref_mock.assert_called_with(db_ref, True)
        # 3. mongo dict with ref and list of refs
        result = BPM._replace_refs_with_models({"test": [db_ref, db_ref]})
        self.assertEqual({"test": [_from_ref_mock.return_value, _from_ref_mock.return_value]}, result)
        BPM._get_type_by_collection.assert_called_with(db_ref.collection)
        # 4. mongo dict with ref and list of refs and dict with refs
        result = BPM._replace_refs_with_models({"test": [db_ref, db_ref], "test2": {"test3": db_ref}})
        self.assertEqual({"test": [_from_ref_mock.return_value, _from_ref_mock.return_value],
                            "test2": {"test3": _from_ref_mock.return_value}}, result)
        BPM._get_type_by_collection.assert_called_with(db_ref.collection)
        # 5. mongo dict with dict with dict with ref
        result = BPM._replace_refs_with_models({"test": {"test2": {"test3": db_ref}}})
        self.assertEqual({"test": {"test2": {"test3": _from_ref_mock.return_value}}}, result)
        BPM._get_type_by_collection.assert_called_with(db_ref.collection)
        # 6. model as dict
        with patch("pydantic_mongo.base_pm_model.DbRefModel", autospec=True) as DbRefModelMock:
            instance = DbRefModelMock.return_value
            instance.model_dump.return_value = "test"
            result = BPM._replace_refs_with_models({"test": db_ref}, model="dict")
            self.assertEqual({"test": "test"}, result)
            DbRefModelMock.assert_called()
            instance.model_dump.assert_called()

    def test_process_mongo_doc(self):
        return_value = {"test": "test"}
        with patch.object(BasePydanticMongoModel, '_replace_refs_with_models',
                          return_value=return_value) as mock_replace:
            result = BasePydanticMongoModel._process_mongo_doc(return_value, as_dict=True)
            self.assertEqual(return_value, result)
            mock_replace.assert_called_with(return_value)

            with self.assertRaises(PydanticValidationError):
                BasePydanticMongoModel._process_mongo_doc(return_value)

    def test_model_dump(self):
        class MongoModelMock(MagicMock):
            model_dump_db = MagicMock(return_value="test")

        test = BasePydanticMongoModel()
        result = test._model_dump(False)
        self.assertEqual({"id": None}, result)

        with patch.object(test, '_MongoModel', MongoModelMock):
            result = test._model_dump(True)
            self.assertEqual(MongoModelMock.model_dump_db(), result)
            self.assertEqual({"id": None}, test._model_dump(False))

    # def test__init_mongo_model(self):
    #     FIXME: test breaks other tests
    #     with patch("pydantic_mongo.mongo_model.MongoModel.from_model", return_value="test") as from_model_mock:
    #         BasePydanticMongoModel._init_mongo_model()
    #
    #         from_model_mock.assert_called_once()
    #         self.assertEqual("test", BasePydanticMongoModel._MongoModel)
    #         from_model_mock.assert_called_once_with(BasePydanticMongoModel)

    def test_model_json_schema(self):
        BPM = BasePydanticMongoModel
        result = BPM._model_json_schema()
        self.assertTrue(isinstance(result, dict))
        self.assertTrue("id" in result["properties"])

        with patch.object(BPM, '_init_mongo_model', MagicMock()):
            model_json_schema_mock = MagicMock(return_value="test")

            with patch.object(BPM, '_MongoModel', MagicMock(model_json_schema=model_json_schema_mock)):
                result = BPM._model_json_schema(True)
                self.assertEqual("test", result)
                BPM._MongoModel.model_json_schema.assert_called_with()


if __name__ == '__main__':
    unittest.main()
