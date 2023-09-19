import datetime
import inspect
from types import NoneType, UnionType
from typing import *

from pydantic import BaseModel

from pydantic_mongo.extensions import ValidationError
from pydantic_mongo.helpers import replace_word

supported_types = [
    int, str, float, bool, list, dict, tuple, List, Tuple, NoneType, Dict, Optional, Union, datetime.date, UnionType,
    ForwardRef
]
module_types = ['__Base', 'BasePydanticMongoModel']
T = TypeVar('T')


class BaseMeta(type(BaseModel)):
    collection_type_map: Dict[str, Type[T]] = {}
    instances: List[str] = []

    def __new__(mcls, name, bases, class_dict, **kwargs):
        mcls.instances.append(name)
        temp_class = type('TempClass', (), {"__annotations__": class_dict.get('__annotations__', {})})
        mcls.check_types(temp_class.__annotations__)

        cls: T = super().__new__(mcls, name, bases, class_dict, **kwargs)
        if name not in module_types:
            mcls.collection_type_map[getattr(cls, "collection_name")] = cls

        return cls

    @classmethod
    def check_types(cls, annotations: Dict[str, Any]):
        """
        Check if types in annotations are supported

        Args:
            annotations: dict with annotations

        Returns:
            None
        """
        raise_error = False
        for field_name, field_type in annotations.items():
            if field_name.startswith("_"):
                continue

            if isinstance(field_type, str):
                for inst in cls.instances:
                    field_type = replace_word(field_type, inst, "type(None)")
            try:
                field_type = field_type if not isinstance(field_type, str) else eval(field_type, locals(), globals())
            except NameError:
                raise_error = True
            if not cls.check_type_recursive(field_type, supported_types):
                raise_error = True

            if raise_error:
                print(field_type, type(field_type))
                raise ValidationError(f"Type {field_type} of field {field_name} is not supported. \n\nSupported types: "
                                      f"{supported_types}")

    @classmethod
    def check_type_recursive(cls, t: type, available_types: List[type]) -> bool:
        """
        Check if a type is supported

        Args:
            t: type to check
            available_types: list with supported types

        Returns:
            True if supported, False otherwise
        """
        if hasattr(t, "__origin__"):
            return all(cls.check_type_recursive(arg, available_types) for arg in t.__args__)
        else:
            if type(t) == ForwardRef:
                return True
            if t not in available_types:
                return inspect.isclass(t) and isinstance(t, BaseMeta)
            return True
