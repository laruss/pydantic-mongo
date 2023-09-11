import unittest

from pydantic_mongo.extensions import PydanticMongo, ValidationError
from tests.unit.base import BaseTest


class TestExtensions(BaseTest):
    def test_init(self):
        PydanticMongo().mongo = None
        pydantic_mongo = PydanticMongo()
        self.assertIsNone(pydantic_mongo.db)

        pydantic_mongo.init_app(self.app)
        self.assertIsNotNone(pydantic_mongo.db)

    def test_singleton(self):
        pydantic_mongo_1 = PydanticMongo()
        pydantic_mongo_2 = PydanticMongo()
        self.assertIs(pydantic_mongo_1, pydantic_mongo_2)

    def test_singleton_init_app(self):
        pydantic_mongo_1 = PydanticMongo()
        pydantic_mongo_1.init_app(self.app)
        pydantic_mongo_2 = PydanticMongo()
        self.assertIs(pydantic_mongo_1, pydantic_mongo_2)
        self.assertIsNotNone(pydantic_mongo_2.db)

    def test_validation_error(self):
        with self.assertRaises(ValidationError):
            raise ValidationError("Some error")

        with self.assertRaises(TypeError):
            raise ValidationError()


if __name__ == '__main__':
    unittest.main()
