import unittest
from typing import Any

from pydantic_mongo.base import __Base as Base
from pydantic_mongo.db_ref_model import DbRefModel
from tests.base import BaseTest


class TestDbRefModel(BaseTest):
    def test_from_model(self):
        class User(Base):
            pass

        result = DbRefModel.from_model(User)
        self.assertEqual(result.__name__, "DbRefModel")
        self.assertEqual(result.__base__, DbRefModel)
        self.assertEqual(result.__annotations__, {"collection": str, "id": Any, "database": str})
        self.assertTrue(issubclass(result, DbRefModel))


if __name__ == '__main__':
    unittest.main()
