import logging
import re
from typing import Callable, get_origin, Iterator, Union, Any, Iterable

from bson import DBRef

logger = logging.getLogger(__name__)


def change_subtypes(t: type, callback: Callable[[type], type]) -> type:
    """
    Change subtypes of type t with returned from callback
    :param t: type
    :param callback: function that takes type and returns type
    :return: new type
    """
    if hasattr(t, "__origin__"):
        new_args = tuple(change_subtypes(arg, callback) for arg in t.__args__)
        origin = get_origin(t)
        return origin[new_args] if origin else t
    else:
        return callback(t)


def find_instance_in_data_and_replace(data: dict, tp: type, callback: Callable[[Any], Any]) -> dict:
    """
    Find all instances of type in data and replace them with callback

    Args:
        data: dict with data
        tp: type to find
        callback: function that takes type and returns type

    Returns:
        dict with replaced types
    """
    for key, value in data.items():
        if isinstance(value, tp):
            data[key] = callback(value)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, tp):
                    data[key][i] = callback(item)
        elif isinstance(value, dict):
            data[key] = find_instance_in_data_and_replace(value, tp, callback)

    return data


def replace_word(input_str: str, target_word: str, replacement: str) -> str:
    """
    Replace full word in string

    Example:
        replace_word("hello, hello2", "hello", "world") -> "world, hello2"

    Args:
        input_str: input string
        target_word: word to replace
        replacement: replacement

    Returns:
        replaced string
    """
    pattern = r'\b' + re.escape(target_word) + r'\b'
    return re.sub(pattern, replacement, input_str)


def get_refs_from_data(data: Union[dict, list, DBRef]) -> Iterator[DBRef]:
    """
    Get all DBRefs from data

    Args:
        data: dict, list or DBRef

    Returns:
        iterator with DBRefs
    """
    if isinstance(data, DBRef):
        yield data
    elif isinstance(data, dict):
        for value in data.values():
            yield from get_refs_from_data(value)
    elif isinstance(data, list):
        for item in data:
            yield from get_refs_from_data(item)


def find_data_with_fields_in_data_and_replace(
        data: dict, fields: Iterable, replace_callback: Callable[[Any], Any]) -> dict:
    """
    Find data with fields in data and replace them with callback

    Args:
        data: dict with data
        fields: fields to find
        replace_callback: function that takes type and returns type

    Returns:
        dict with replaced types
    """
    if all([field in data for field in fields]):
        return replace_callback(data)
    for key, value in data.items():
        if isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    data[key][i] = find_data_with_fields_in_data_and_replace(item, fields, replace_callback)
        elif isinstance(value, dict):
            data[key] = find_data_with_fields_in_data_and_replace(value, fields, replace_callback)

    return data
