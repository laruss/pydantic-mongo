import unittest

from pydantic_mongo.base_pm_model import BasePydanticMongoModel
from tests.base import BaseTest

schema = {'$defs': {'ParentModel': {'additionalProperties': False, 'properties': {
    '_id': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'default': None, 'title': ' Id'},
    'name': {'title': 'Name', 'type': 'string'}}, 'required': ['name'], 'title': 'ParentModel', 'type': 'object'}},
          'additionalProperties': False,
          'properties': {'_id': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'default': None, 'title': ' Id'},
                         'name': {'title': 'Name', 'type': 'string'}, 'parent': {'$ref': '#/$defs/ParentModel'}},
          'required': ['name', 'parent'], 'title': 'TestModel', 'type': 'object'}

mongo_schema = {'$defs': {'DbRefModel': {
    'properties': {'collection': {'default': 'parent_models', 'title': 'Collection', 'type': 'string'},
                   'id': {'title': 'Id'}, 'database': {'default': None, 'title': 'Database', 'type': 'string'}},
    'required': ['id'], 'title': 'DbRefModel', 'type': 'object'}},
                'properties': {'id': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'title': 'Id'},
                               'name': {'title': 'Name', 'type': 'string'}, 'parent': {'$ref': '#/$defs/DbRefModel'}},
                'required': ['id', 'name', 'parent'], 'title': 'MongoModel', 'type': 'object'}


class TestBasePydanticMongoModel(BaseTest):
    def get_test_model(self):
        class ParentModel(BasePydanticMongoModel):
            name: str

        class TestModel(BasePydanticMongoModel):
            name: str
            parent: ParentModel

        parent = ParentModel(name="parent")

        return TestModel(name="test", parent=parent)

    def test_model_init(self):
        model = BasePydanticMongoModel()
        self.assertIsNotNone(model._MongoModel)

        model = self.get_test_model()
        self.assertIsNotNone(model._MongoModel)
        self.assertEqual(model.name, "test")
        self.assertTrue("name" in model._MongoModel.model_fields)

    def test_model_dump(self):
        self.assertEqual(
            self.get_test_model().model_dump(as_mongo_model=True),
            {'name': 'test', 'parent': {'collection': 'parent_models', 'id': None, 'database': None}}
        )
        self.assertEqual(
            self.get_test_model().model_dump(),
            {'id': None, 'name': 'test', 'parent': {'id': None, 'name': 'parent'}}
        )

    def test_model_json_schema(self):
        self.assertEqual(self.get_test_model().model_json_schema(), schema)
        self.assertEqual(self.get_test_model().model_json_schema(as_mongo_model=True), mongo_schema)


if __name__ == '__main__':
    unittest.main()
