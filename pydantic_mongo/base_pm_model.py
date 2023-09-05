from __future__ import annotations

import logging
import typing
from typing import Optional, Any, Type, Mapping, Union

from pydantic import create_model
from pydantic.fields import FieldInfo

from pydantic_mongo.base import __Base as Base
from pydantic_mongo.helpers import replace_refs_with_models, replace_object_id_in_dict, find_descendants_in_types
from pydantic_mongo.mongo_model import MongoModel

logger = logging.getLogger(__name__)


class BasePydanticMongoModel(Base):
    _MongoModel: Optional[Type[MongoModel]] = None

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._MongoModel = MongoModel.from_model(self.__class__)

    @classmethod
    def _find_descendants_in_types(cls, type_dict: dict[str, FieldInfo],
                                   data_dict: typing.Dict[str, Any],
                                   search_cls: type = Base
                                   ) -> typing.Tuple[typing.Dict[str, typing.Tuple[type, Ellipsis]], bool]:
        """
        See pydantic_mongo.helpers.find_descendants_in_types docstring
        """
        return find_descendants_in_types(type_dict, data_dict, search_cls)

    @classmethod
    def __init_mongo_model(cls):
        cls._MongoModel = MongoModel.from_model(cls)

    @classmethod
    def _strip_mongo_doc(cls, mongo_doc: Mapping[str, Any]) -> dict[str, Any]:
        mongo_doc = dict(mongo_doc)
        model_from_db = replace_refs_with_models(mongo_doc, cls.__mongo__.db)
        model_from_db = replace_object_id_in_dict(model_from_db)

        return model_from_db

    @classmethod
    def _process_mongo_doc(cls, mongo_doc: Mapping[str, Any]):
        mongo_doc = cls._strip_mongo_doc(mongo_doc)
        fields_as_definitions, changed = cls._find_descendants_in_types(cls.model_fields, mongo_doc)
        if changed:
            logger.warning(f"Model {cls.__name__} has changed. Creating new model with fields: {fields_as_definitions}")
            del fields_as_definitions["id"]
            OptionalModel = create_model(cls.__class__.__name__, __base__=cls, **fields_as_definitions)
            return OptionalModel(**mongo_doc)

        return cls(**mongo_doc)

    def model_dump(self, as_mongo_model: bool = False, **kwargs) -> dict[str, Any]:
        """
        Dump model to dict
        :param as_mongo_model: if True, return dict with MongoModel
        :param kwargs: kwargs for super().model_dump
        :return: dict
        """
        self_dict = super().model_dump(**kwargs)
        if as_mongo_model:
            return self._MongoModel(**self_dict).model_dump_db(convert_to_db=False)
        return self_dict

    @classmethod
    def model_json_schema(cls, as_mongo_model: bool = False, **kwargs) -> dict[str, Any]:
        """
        Get model json schema
        :param as_mongo_model: if True, return dict with MongoModel
        :param kwargs: kwargs for super().model_json_schema
        :return: dict
        """
        if as_mongo_model:
            cls.__init_mongo_model()
            schema = cls._MongoModel.model_json_schema(**kwargs)
        else:
            schema = super(BasePydanticMongoModel, cls).model_json_schema(**kwargs)

        return schema
