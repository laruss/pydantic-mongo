import unittest
from typing import List, Tuple, Dict, Optional

from pydantic_mongo.helpers import *
from tests.unit.base import BaseTestWithData


class TestHelpers(BaseTestWithData):
    def test_change_subtypes(self):
        result = change_subtypes(int, lambda x: str)
        self.assertEqual(result, str)
        result = change_subtypes(List[int], lambda x: str if x is int else x)
        self.assertEqual(result, list[str])
        result = change_subtypes(Dict[str, Tuple[int, float]],
                                 lambda x: str if x is int else x)
        self.assertEqual(result, dict[str, tuple[str, float]])
        result = change_subtypes(Union[int, float], lambda x: str if x is int else x)
        self.assertEqual(result, Union[str, float])
        result = change_subtypes(str, lambda x: x)
        self.assertEqual(result, str)
        result = change_subtypes(Dict[str, List[Union[int, float]]],
                                 lambda x: str if x is int else x)
        self.assertEqual(result, dict[str, list[Union[str, float]]])
        result = change_subtypes(Optional[int],
                                 lambda x: str if x is int else x)
        self.assertEqual(result, Optional[str])
        result = change_subtypes(Union[int, Tuple[float, str]],
                                 lambda x: List[x] if x is int else x)
        self.assertEqual(result, Union[List[int], tuple[float, str]])

    def test_find_instance_in_data_and_replace(self):
        def callback_fn(value):
            return str(value)

        data1 = {
            "key1": 123,
            "key2": "string",
            "key3": 456
        }
        result1 = find_instance_in_data_and_replace(data1, int, callback_fn)
        self.assertEqual(result1, {
            "key1": "123",
            "key2": "string",
            "key3": "456"
        })

        data2 = {
            "key1": [1, 2, "string", 3],
            "key2": "string"
        }
        result2 = find_instance_in_data_and_replace(data2, int, callback_fn)
        self.assertEqual(result2, {
            "key1": ["1", "2", "string", "3"],
            "key2": "string"
        })

        data3 = {
            "key1": {
                "sub_key1": 123,
                "sub_key2": [1, 2, 3],
                "sub_key3": {
                    "sub_sub_key": 456
                }
            },
            "key2": "string"
        }
        result3 = find_instance_in_data_and_replace(data3, int, callback_fn)
        self.assertEqual(result3, {
            "key1": {
                "sub_key1": "123",
                "sub_key2": ["1", "2", "3"],
                "sub_key3": {
                    "sub_sub_key": "456"
                }
            },
            "key2": "string"
        })

    def test_replace_word(self):
        test_string = "Model1 Model2 Model3"

        self.assertEqual(replace_word(test_string, "Model1", "Model4"),
                         "Model4 Model2 Model3")
        self.assertEqual(replace_word(test_string, "Model", "Model4"),
                         test_string)

    def test_get_refs_from_data(self):
        db_ref_a1 = DBRef("a", "1")
        db_ref_b2 = DBRef("b", "2")
        db_ref_c3 = DBRef("c", "3")
        db_ref_d4 = DBRef("d", "4")
        data = {
            "a": db_ref_a1,
            "b": db_ref_b2,
            "c": [
                db_ref_c3,
                db_ref_d4
            ]
        }
        result = list(get_refs_from_data(data))
        self.assertEqual(result, [db_ref_a1, db_ref_b2, db_ref_c3, db_ref_d4])

        complex_data = {
            "a": db_ref_a1,
            "b": {
                "c": [
                    db_ref_c3,
                ],
                "d": db_ref_d4
            },
            "c": [
                db_ref_b2,
                {
                    "d": db_ref_d4
                }
            ]
        }
        result = list(get_refs_from_data(complex_data))
        self.assertEqual([db_ref_a1, db_ref_c3, db_ref_d4, db_ref_b2, db_ref_d4], result)


if __name__ == '__main__':
    unittest.main()
