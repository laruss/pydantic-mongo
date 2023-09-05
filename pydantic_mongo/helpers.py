import logging
from typing import Dict, Any, Union, Tuple, Optional

import pymongo.database
from bson import DBRef, ObjectId
from pydantic.fields import FieldInfo

from pydantic_mongo.base import __Base as Base

logger = logging.getLogger(__name__)

IncEx = "set[int] | set[str] | dict[int, Any] | dict[str, Any] | None | list[int] | list[str]"


def replace_refs_with_models(data: Dict[str, Any], db: pymongo.database.Database) -> Dict[str, any]:
    """
    Replace DBRef with model data or None if not found
    :param data: dict with data from mongo
    :param db: pymongo database
    :return: dict
    """
    for key, value in data.items():
        if isinstance(value, DBRef):
            child_data = db[value.collection].find_one({"_id": ObjectId(value.id)})
            if not child_data:
                logger.warning(f"Child data not found for {value}")
                data[key] = None
                continue
            data[key] = replace_refs_with_models(child_data, db) if child_data else child_data
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, DBRef):
                    child_data = db[item.collection].find_one({"_id": ObjectId(item.id)})
                    data[key][i] = replace_refs_with_models(child_data, db) if child_data else child_data
        elif isinstance(value, dict):
            data[key] = replace_refs_with_models(value, db)

    return data


def replace_object_id_in_dict(data: dict) -> dict:
    """
    Replace ObjectId with str in dictionary
    :param data: dict with data
    :return: dict with str instead of ObjectId
    """
    for key, value in data.items():
        if isinstance(value, ObjectId):
            data[key] = str(value)
        elif isinstance(value, list):
            data[key] = replace_object_id_in_list(value)
        elif isinstance(value, dict):
            data[key] = replace_object_id_in_dict(value)

    return data


def replace_object_id_in_list(data: list) -> list:
    """
    Replace ObjectId with str in list
    :param data: list with data
    :return: list with str instead of ObjectId
    """
    for i, item in enumerate(data):
        if isinstance(item, ObjectId):
            data[i] = str(item)
        elif isinstance(item, list):
            data[i] = replace_object_id_in_list(item)
        elif isinstance(item, dict):
            data[i] = replace_object_id_in_dict(item)

    return data


def contains_subclass_of(base_cls: type, check_cls: Union[type, FieldInfo]) -> bool:
    """
    Check if check_cls is subclass of base_cls
    :param base_cls: type
    :param check_cls: type or FieldInfo
    :return: bool whether check_cls is subclass of base_cls
    """
    if isinstance(check_cls, FieldInfo):
        return contains_subclass_of(base_cls, check_cls.annotation)

    if isinstance(check_cls, type):
        try:
            return issubclass(check_cls, base_cls)
        except TypeError:
            return False

    if hasattr(check_cls, "__origin__"):
        if check_cls.__origin__ in [list, dict, set, tuple]:
            return any(contains_subclass_of(base_cls, arg) for arg in check_cls.__args__)

        if check_cls.__origin__ is Union:
            return any(contains_subclass_of(base_cls, arg) for arg in check_cls.__args__)

        return contains_subclass_of(base_cls, check_cls.__origin__)

    return False


def find_descendants_in_types(type_dict: dict[str, FieldInfo],
                              data_dict: Dict[str, Any],
                              search_cls: type = Base
                              ) -> Tuple[Dict[str, Tuple[type, Ellipsis]], bool]:
    """
    Find descendants of search_cls in type_dict and data_dict
    :param type_dict: dictionary with field names as keys and types as values
    :param data_dict: dictionary with field names as keys and data as values
    :param search_cls: type to search for
    :return: tuple with dictionary with field names as keys and tuple with type and Ellipsis as values and bool whether
             model has changed
    """
    fields_as_definitions = {}
    changed = False

    for field_name, field in type_dict.items():
        if not contains_subclass_of(search_cls, field):
            fields_as_definitions[field_name] = (field.annotation, Ellipsis)
        else:
            data = data_dict.get(field_name)
            if data is not None:
                fields_as_definitions[field_name] = (field.annotation, Ellipsis)
            else:
                optional_annotation = Optional[field.annotation]
                fields_as_definitions[field_name] = (optional_annotation, Ellipsis)
                changed = True

    return fields_as_definitions, changed
