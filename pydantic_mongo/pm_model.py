from __future__ import annotations

from bson import ObjectId, DBRef
from typing import Optional, Union, Any, Iterator, Dict, List, TypeVar, Type

from pydantic_mongo.base_pm_model import BasePydanticMongoModel

T = TypeVar("T", bound="PydanticMongoModel")


class PydanticMongoModel(BasePydanticMongoModel):
    @classmethod
    def get_by_id(cls: Type[T], _id: Union[str, ObjectId]) -> Optional[T]:
        """
        Get model by id from database

        Args:
            _id: id as str or ObjectId

        Returns:
            None if not found else Model
        """
        return cls.get_by_filter({"_id": _id})

    @classmethod
    def from_ref(cls: Type[T], ref: DBRef, unloaded: bool = True) -> T:
        """
        Get model from DBRef.
        The Model won't be loaded from db until you try to access its public attribute if unloaded is True.
        Else model will be loaded from db immediately

        Args:
            ref: bson.DBRef(collection: str, id: str)
            unloaded: if True, a model will be unloaded (by default), else it will be loaded from db

        Returns:
            Model, created by pydantic `create_model`
        """
        return cls._from_ref(ref, unloaded)

    @classmethod
    def get_with_parse_db_refs(cls: Type[T], data: dict) -> T:
        """
        Get model from dict if db_refs are presented as dict with three keys: id, collection, database

        Args:
            data: model data dict

        Returns:
            Model
        """
        return cls._get_with_parse_db_refs(data)

    @property
    def db_ref(self) -> DBRef:
        """
        Get DBRef for a model if id is not None

        Returns:
            bson.DBRef(collection: str, id: str)
        """
        return super().db_ref

    @classmethod
    def get_by_filter(cls: Type[T], filter: Dict[str, Any]) -> Optional[T]:
        """
        Get model by filter from database
        Args:
            filter: filter dict

        Returns:
            None if not found else Model
        """
        return cls._get_by_filter(filter)

    def get_ref_objects(self: T) -> Optional[List[Optional[T]]]:
        """
        Get all ref objects from a model.

        Returns:
            list with models or None if not found
        """
        if self.id is None:
            return None

        mongo_doc = self.collection().find_one({"_id": ObjectId(self.id)})
        if not mongo_doc:
            return None

        return self._get_ref_objects(dict(mongo_doc))

    def save(self: T) -> T:
        """
        Save model to database

        Returns:
            PydanticMongoModel
        """
        return self._save()

    def delete(self) -> None:
        """
        Delete model from database

        Returns:
            None
        """
        if self.id is not None:
            obj_id = ObjectId(self.id)
            self.collection().delete_one({"_id": obj_id})

    @classmethod
    def objects(cls: Type[T], filter: Optional[Dict[str, Any]] = None) -> Iterator[T]:
        """
        Get all models from database
        Args:
            filter: filter dict

        Returns:
            iterator with models
        """
        return cls._objects(filter)

    def model_dump(self, as_mongo_model: bool = False, **kwargs) -> dict[str, Any]:
        """Usage docs: https://docs.pydantic.dev/2.2/usage/serialization/#modelmodel_dump

        DOCS FROM PYDANTIC:

        Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.

        Args:
            as_mongo_model: if True, return dict with MongoModel
            kwargs:
                mode: The mode in which `to_python` should run.
                If mode is 'json', the dictionary will only contain JSON serializable types.
                If mode is 'python', the dictionary may contain any Python objects.
                include: A list of fields to include in the output.
                by_alias: Whether to use the field's alias in the dictionary key if defined.
                exclude_unset: Whether to exclude fields that are unset or None from the output.
                exclude_defaults: Whether to exclude fields that are set to their default value from the output.
                exclude_none: Whether to exclude fields that have a value of `None` from the output.
                round_trip: Whether to enable serialization and deserialization round-trip support.
                warnings: Whether to log warnings when invalid fields are encountered.

        Returns:
            A dictionary representation of the model.
        """
        return self._model_dump(as_mongo_model=as_mongo_model, **kwargs)

    @classmethod
    def model_json_schema(cls, as_mongo_model: bool = False, by_alias: bool = False, **kwargs) -> dict[str, Any]:
        """Generates a JSON schema for a model class.

        DOCS FROM PYDANTIC:

        Args:
            as_mongo_model: if True, return dict with MongoModel
            by_alias: Whether to use attribute aliases or not.
            kwargs:
                ref_template: The reference template.
                schema_generator: To override the logic used to generate the JSON schema, as a subclass of
                    `GenerateJsonSchema` with your desired modifications
                mode: The mode in which to generate the schema.

        Returns:
            The JSON schema for the given model class.
        """
        return cls._model_json_schema(as_mongo_model=as_mongo_model, by_alias=by_alias, **kwargs)
