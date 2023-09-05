from __future__ import annotations

from typing import Optional, Dict, get_origin, Type, Tuple, Any, Union

from bson import DBRef
from pydantic import BaseModel, Field, create_model
from pydantic.fields import FieldInfo

from pydantic_mongo.base import __Base as Base
from pydantic_mongo.db_ref_model import DbRefModel


class MongoModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)

    class Config:
        populate_by_name = True
        from_attributes = True

    def model_dump(self, **kwargs):
        return super().model_dump(by_alias=True, **kwargs)

    @classmethod
    def _is_complex_type(cls, annotation):
        return hasattr(annotation, "__args__")

    @classmethod
    def _get_fields_from_annotation(
            cls,
            field: str,
            annotation: FieldInfo.annotation,
            replacing_type: Type[DbRefModel],
            replaceable_type: Type[Base] = Base
    ) -> Dict[str, Tuple[Type, Any]]:
        """
        Get fields from FieldInfo annotation
        :param field: field name, str
        :param annotation: pydantic field annotation
        :param replacing_type: DBRef-inherited model
        :param replaceable_type: Base-inherited model
        :return: dict with field name as key and tuple with type and default value as value
        """
        new_type = annotation
        if cls._is_complex_type(annotation):
            new_args = [
                replacing_type.from_model(arg) if issubclass(arg, replaceable_type) else arg
                for arg in annotation.__args__
            ]
            origin = get_origin(annotation)
            if origin:
                new_type = origin[tuple(new_args)]
        else:
            if issubclass(annotation, replaceable_type):
                new_type = replacing_type.from_model(annotation)

        return {field: (new_type, ...)}

    @classmethod
    def _get_fields_validators_from_annotation(
            cls,
            annotation: FieldInfo.annotation,
            replacing_type: Type[DbRefModel],
            replaceable_type: Type[Base] = Base
    ) -> Optional[callable]:
        """
        Get validator for replacing model with DBRef
        :param annotation: pydantic field annotation
        :param replacing_type: DBRef-inherited model
        :param replaceable_type: Base-inherited model
        :return: validator
        """
        replacer = lambda x: replacing_type(collection=x.collection_name, id=x.id) if isinstance(x, replaceable_type) else x
        dict_replacer = lambda x: {k: replacer(v) for k, v in x.items()}
        list_replacer = lambda x: [replacer(v) for v in x]

        if cls._is_complex_type(annotation):
            origin = get_origin(annotation)
            if origin:
                if origin is dict:
                    return dict_replacer
                if origin is list:
                    return list_replacer
                return replacer
        else:
            if issubclass(annotation, replaceable_type):
                return replacer

    def _convert_to_db_ref_if_needed(self, data: Dict[str, Any]) -> Union[Dict[str, Any], DBRef]:
        """
        Convert model to dict with DBRef instead of models
        :param data: dictionary with model data
        :return: dict or DBRef
        """
        replaceable_fields = list(DbRefModel.model_fields.keys())
        data_fields = list(data.keys())

        if len(data_fields) == len(replaceable_fields) and set(data_fields) == set(replaceable_fields):
            if data["id"] is None:
                raise ValueError(f"Object id is None for data {data}. Did you forget to save it?")
            return DBRef(collection=data["collection"], id=data["id"], database=data["database"])

        for field in data_fields:
            if isinstance(data[field], dict):
                data[field] = self._convert_to_db_ref_if_needed(data[field])
            elif isinstance(data[field], list):
                for i, item in enumerate(data[field]):
                    if isinstance(item, dict):
                        data[field][i] = self._convert_to_db_ref_if_needed(item)

        return data

    def model_dump_db(self, convert_to_db: bool = True) -> dict[str, Any]:
        """
        Dump model to dict with DBRef instead of models
        :param convert_to_db: if True, return DBRef instead of DBRefModel
        :return: dict
        """
        _model = self.model_dump(exclude={"id"})
        return self._convert_to_db_ref_if_needed(_model) if convert_to_db else _model

    @classmethod
    def from_model(cls: Type[MongoModel], model: Type[Base]) -> Type[MongoModel]:
        """
        Create MongoModel class from Base-inherited model
        :param model: Base-inherited model
        :return: MongoModel as type
        """
        replacing_type = DbRefModel
        model_fields = model.model_fields
        new_model_fields = {}
        new_model_validators = {}
        for field, an in model_fields.items():
            new_field_data = cls._get_fields_from_annotation(field, an.annotation, replacing_type)
            new_model_fields.update(new_field_data)
            new_validator = cls._get_fields_validators_from_annotation(an.annotation, replacing_type)
            if new_validator:
                new_model_validators[field] = new_validator

        return create_model(
            'MongoModel',
            __validators__=new_model_validators,
            __base__=cls,
            **new_model_fields
        )