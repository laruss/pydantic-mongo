from __future__ import annotations

from bson import ObjectId
from typing import Optional, Union, Any, Iterator, Dict

from pydantic_mongo.base_pm_model import BasePydanticMongoModel


class PydanticMongoModel(BasePydanticMongoModel):
    @classmethod
    def get_by_id(cls, _id: Union[str, ObjectId]) -> Optional[PydanticMongoModel]:
        """
        Get model by id from database

        :param _id: str, ObjectId, PydanticObjectId
        :return: Model or None
        """
        return cls.get_by_filter({"_id": _id})

    @classmethod
    def _get_id_as_object_id(cls, id_value: Any):
        assert isinstance(id_value, (str, ObjectId)), f"Invalid id {id_value}. Must be str or ObjectId"
        return ObjectId(id_value) if isinstance(id_value, str) else id_value

    @classmethod
    def get_by_filter(cls, filter: Dict[str, Any]) -> Optional[PydanticMongoModel]:
        if "_id" in filter:
            filter["_id"] = cls._get_id_as_object_id(filter["_id"])

        mongo_doc = cls.collection().find_one(filter)
        if not mongo_doc:
            return None

        return cls._process_mongo_doc(mongo_doc)

    def save(self) -> PydanticMongoModel:
        """
        Save model to database
        :return: PydanticMongoModel
        """
        data = self._MongoModel(**self.model_dump()).model_dump_db()
        collection = self.collection()
        if self.id is None:
            result = collection.insert_one(data)
            self.id = str(result.inserted_id)
        else:
            obj_id = self._get_id_as_object_id(self.id)
            collection.update_one({"_id": obj_id}, {"$set": data})

        return self

    def delete(self) -> None:
        """
        Delete model from database
        :return: None
        """
        if self.id is not None:
            obj_id = self._get_id_as_object_id(self.id)
            self.collection().delete_one({"_id": obj_id})

    @classmethod
    def objects(cls, filter: Optional[Dict[str, Any]] = None) -> Iterator[PydanticMongoModel]:
        """
        Get all models from database
        :param filter: dict
        :return: Iterator[Model]
        """
        filter = filter or {}
        if "_id" in filter:
            filter["_id"] = cls._get_id_as_object_id(filter["_id"])

        for mongo_doc in cls.collection().find(filter or {}):
            yield cls._process_mongo_doc(mongo_doc)

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
        return super().model_dump(as_mongo_model=as_mongo_model, **kwargs)

    @classmethod
    def model_json_schema(cls, as_mongo_model: bool = False, **kwargs) -> dict[str, Any]:
        """Generates a JSON schema for a model class.

        DOCS FROM PYDANTIC:

        Args:
            as_mongo_model: if True, return dict with MongoModel
            kwargs:
                by_alias: Whether to use attribute aliases or not.
                ref_template: The reference template.
                schema_generator: To override the logic used to generate the JSON schema, as a subclass of
                    `GenerateJsonSchema` with your desired modifications
                mode: The mode in which to generate the schema.

        Returns:
            The JSON schema for the given model class.
        """
        return super(PydanticMongoModel, cls).model_json_schema(as_mongo_model=as_mongo_model, **kwargs)
