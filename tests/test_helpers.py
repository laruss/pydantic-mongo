import unittest
from typing import List

from pydantic_mongo.helpers import *
from tests.base import BaseTestWithData


class TestHelpers(BaseTestWithData):
    def test_replace_refs_with_models(self):
        data = [
            ({}, {}),
            ({"test": "test"}, {"test": "test"}),
            (self.doc_dict, self.doc_dict_final),
            (self.doc_collection_dict_final, self.doc_collection_dict_final),
            ({"test": DBRef("test", "64f6046aee53622e29af34bb")}, {"test": None}),
        ]

        with self.assertRaises(AttributeError):
            replace_refs_with_models(None, self.mongo.db)

        for test_item in data:
            if "_id" in test_item[0]:
                del test_item[0]["_id"]
            result = replace_refs_with_models(test_item[0], self.mongo.db)
            self.assertEqual(result, test_item[1])

    def test_replace_object_id_in_dict(self):
        data = [
            ({}, {}),
            ({"test": "test"}, {"test": "test"}),
            ({"test": self.user.inserted_id}, {"test": str(self.user.inserted_id)}),
            ({"test": [self.user.inserted_id]}, {"test": [str(self.user.inserted_id)]}),
            ({"test": {"test": self.user.inserted_id}}, {"test": {"test": str(self.user.inserted_id)}}),
            (self.doc_collection_dict_final, self.doc_collection_dict_final_str)
        ]

        with self.assertRaises(AttributeError):
            replace_object_id_in_dict(None)

        for test_item in data:
            if "_id" in test_item[0]:
                del test_item[0]["_id"]

            result = replace_object_id_in_dict(test_item[0])
            self.assertEqual(result, test_item[1])

    def test_contains_subclass_of(self):
        class Base:
            pass

        class Derived(Base):
            pass

        class NotDerived:
            pass

        self.assertTrue(contains_subclass_of(Base, Derived))
        self.assertFalse(contains_subclass_of(Base, NotDerived))

        # test FieldInfo
        derived_info = FieldInfo(annotation=Derived)
        not_derived_info = FieldInfo(annotation=NotDerived)
        self.assertTrue(contains_subclass_of(Base, derived_info))
        self.assertFalse(contains_subclass_of(Base, not_derived_info))

        # test Union
        self.assertTrue(contains_subclass_of(Base, Union[Derived, NotDerived]))
        self.assertFalse(contains_subclass_of(Base, Union[NotDerived, NotDerived]))

        # test Optional
        self.assertTrue(contains_subclass_of(Base, Optional[Derived]))
        self.assertFalse(contains_subclass_of(Base, Optional[NotDerived]))

        # test List
        self.assertTrue(contains_subclass_of(Base, List[Derived]))
        self.assertFalse(contains_subclass_of(Base, list[NotDerived]))

        # test Dict
        self.assertTrue(contains_subclass_of(Base, Dict[str, Derived]))
        self.assertFalse(contains_subclass_of(Base, Dict[str, NotDerived]))

        # test Tuple
        self.assertTrue(contains_subclass_of(Base, Tuple[Derived, Derived]))
        self.assertFalse(contains_subclass_of(Base, Tuple[NotDerived, NotDerived]))

    def test_find_descendants_in_types(self):
        class Base:
            pass

        class Derived(Base):
            pass

        class NotDerived:
            pass

        types = {
            "base_field": FieldInfo(annotation=Base),
            "derived_field": FieldInfo(annotation=Derived),
            "notderived_field": FieldInfo(annotation=NotDerived),
            "list_field": FieldInfo(annotation=List[Derived]),
            "optional_field": FieldInfo(annotation=Optional[Derived])
        }

        data = {
            "base_field": Base(),
            "derived_field": Derived(),
            "notderived_field": NotDerived(),
            "list_field": [Derived()],
            "optional_field": None
        }

        result_definitions, changed = find_descendants_in_types(types, data, Base)

        self.assertIn("base_field", result_definitions)
        self.assertIn("derived_field", result_definitions)
        self.assertIn("notderived_field", result_definitions)
        self.assertIn("list_field", result_definitions)
        self.assertIn("optional_field", result_definitions)

        self.assertEqual(result_definitions["base_field"], (Base, Ellipsis))
        self.assertEqual(result_definitions["derived_field"], (Derived, Ellipsis))
        self.assertEqual(result_definitions["notderived_field"], (NotDerived, Ellipsis))
        self.assertEqual(result_definitions["list_field"], (List[Derived], Ellipsis))
        self.assertEqual(result_definitions["optional_field"], (Optional[Derived], Ellipsis))

        self.assertTrue(changed)

        data["optional_field"] = Derived()

        result_definitions, changed = find_descendants_in_types(types, data, Base)

        self.assertFalse(changed)


if __name__ == '__main__':
    unittest.main()
