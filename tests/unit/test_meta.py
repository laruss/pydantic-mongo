from __future__ import annotations

import datetime
from types import NoneType
from typing import List, Tuple, Dict, Optional, Union

from pydantic import BaseModel

from pydantic_mongo.extensions import ValidationError
from pydantic_mongo.meta import BaseMeta
from tests.unit.base import BaseTest


class TestClass(BaseModel, metaclass=BaseMeta):
    @classmethod
    @property
    def collection_name(cls):
        return ''


class TestMeta(BaseTest):
    def test_class_creation(self):
        class _(metaclass=BaseMeta):
            collection_name = "some_collection"

    def test_class_creation_without_collection_name(self):
        with self.assertRaises(AttributeError):
            class _(metaclass=BaseMeta):
                pass

    def test_class_creation_with_valid_attributes(self):
        class SomeType(TestClass):
            pass

        class _(TestClass):
            name: str
            age: int
            height: float
            is_active: bool
            list_of_ints: list[int]
            list_of_strs: List[str]
            tuple_of_ints: tuple[int]
            tuple_of_strs: Tuple[str]
            none_type: NoneType
            list_of_none_types: list[NoneType]
            list_of_lists_of_ints: list[list[int]]
            list_of_tuples_of_strs: list[Tuple[str]]
            list_of_tuples_of_lists_of_ints: list[Tuple[list[int]]]
            dict_of_items: dict[str, int]
            dict_of_lists_of_ints: dict[str, list[int]]
            dict_typing: Dict[str, int]
            optional_int: Optional[int]
            optional_some_type: Optional[SomeType]
            union_of_int_and_str: Union[int, str]
            datetime_date: datetime.date
            complex_union_type: Union[str, int, List[SomeType], Tuple[SomeType, int]]

    def test_class_creation_with_invalid_attributes(self):
        with self.assertRaises(ValidationError):
            class _(metaclass=BaseMeta):
                collection_name: str = "some_collection"
                some_att: int | str

        with self.assertRaises(ValidationError):
            class _(metaclass=BaseMeta):
                collection_name: str = "some_collection"
                some_att: bytes

        with self.assertRaises(ValidationError):
            class _(metaclass=BaseMeta):
                collection_name: str = "some_collection"
                some_att: Optional[bytes]

        class NoName:
            pass

        with self.assertRaises(ValidationError):
            class _(metaclass=BaseMeta):
                collection_name: str = "some_collection"
                some_att: Union[int, NoName]

    def test_no_error_if_type_is_private(self):
        class _(metaclass=BaseMeta):
            _some_att: bytes
            collection_name: str = ''

        class NoName:
            pass

        class _(metaclass=BaseMeta):
            __some_att: Union[int, NoName]
            collection_name: str = ''
