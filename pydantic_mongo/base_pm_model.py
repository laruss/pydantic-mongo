from __future__ import annotations

import inspect
import logging
import typing
from typing import Optional, Any, Type, Mapping

from bson import DBRef, ObjectId
from pydantic import ValidationError as PydanticValidationError, create_model

from pydantic_mongo.base import __Base as Base
from pydantic_mongo.db_ref_model import DbRefModel
from pydantic_mongo.helpers import get_refs_from_data, find_instance_in_data_and_replace, \
    find_data_with_fields_in_data_and_replace
from pydantic_mongo.mongo_model import MongoModel

logger = logging.getLogger(__name__)
T = typing.TypeVar("T", bound="BasePydanticMongoModel")


class BasePydanticMongoModel(Base):
    _MongoModel: Optional[Type[MongoModel]] = None

    def __init__(self, __is_loaded__: bool = True, **data: Any):
        super().__init__(**data)
        self._MongoModel = MongoModel.from_model(self.__class__)
        self.__is_loaded__ = __is_loaded__
        self.__db_ref__ = None

    def __getattribute__(self, item: str) -> Any:
        """
        Checks if model is loaded from db and loads it if not when trying to get public attribute

        Args:
            item: attribute name, str

        Returns:
            attribute value
        """
        try:
            attr = super().__getattribute__(item)
        except AttributeError as e:
            if not getattr(self, "__is_loaded__", True):
                attr = None
            else:
                raise e
        if item.startswith("_") or item == "model_post_init":
            return attr
        if inspect.isfunction(attr) or inspect.ismethod(attr):
            return attr
        if inspect.ismethoddescriptor(attr):
            return attr
        if isinstance(getattr(self.__class__, item, None), property):
            return attr
        if not getattr(self, "__is_loaded__", True):
            return self._load_from_db(item)
        return attr

    @classmethod
    def _get_with_parse_db_refs(cls: Type[T], data: dict) -> T:
        """
        Get model from dict if db_refs are presented as dict with three keys: id, collection, database

        Args:
            data: model data dict

        Returns:
            Model
        """
        data = cls._parse_db_refs(data)

        return cls(**data)

    @property
    def db_ref(self) -> DBRef:
        """
        Get DBRef for a model if id is not None

        Returns:
            bson.DBRef(collection: str, id: str)
        """
        if self.__db_ref__ is not None:
            return self.__db_ref__
        if self.id is None:
            raise ValueError(f"Can't get DBRef for {self.__class__.__name__} without id. Save model first")
        self.__db_ref__ = DBRef(collection=self.collection_name, id=self.id)

        return self.__db_ref__

    @classmethod
    def _parse_db_refs(cls, data: dict) -> dict:
        """
        Checks if there are dict with 3 keys: id, collection, database and replaces it with db_refs and then with models

        Args:
            data: model data dict

        Returns:
            dict with replaced db_refs as models
        """
        processed_data = find_data_with_fields_in_data_and_replace(
            data,
            fields=["id", "collection", "database"],
            replace_callback=lambda x: DBRef(**x)
        )
        return cls._replace_refs_with_models(processed_data, unloaded=False)

    def _load_from_db(self, item: str):
        """
        Load model from db when trying to access its attribute
        If model is not saved (has no id), raise ValueError
        If data is damaged somehow, return model built with pydantic `model_construct`

        Args:
            item: attribute name, str

        Returns:
            attribute value
        """
        logger.debug(f"Loading {self.__class__.__name__} from db with {item}")
        data: Optional[dict] = self._get_by_filter({"_id": self.db_ref.id}, as_dict=True)
        if data is None:
            logger.warning(f"Can't load {self.__class__.__name__} from db. Check if it is saved")
            self.__dict__ = self.__class__.model_construct().__dict__
            self.__is_loaded__ = True
            return getattr(self, item)
        if data.get("_id"):
            data["id"] = data.pop("_id")
        try:
            self.__dict__ = dict(self.__class__.__dict__)
            self.__init__(**data)
        except PydanticValidationError as e:
            logger.warning(f"Failed to load {self.__class__.__name__} from db with {item}: {e}")
            self.__dict__ = self.__class__.model_construct(**data).__dict__

        self.__is_loaded__ = True
        return getattr(self, item)

    def _save(self) -> T:
        """
        Save model to database

        Returns:
            PydanticMongoModel
        """
        # for loading from db if model is not loaded
        self.__str__()

        data = self._MongoModel(**self.model_dump()).model_dump_db()
        collection = self.collection()
        if self.id is None:
            result = collection.insert_one(data)
            self.id = str(result.inserted_id)
        else:
            obj_id = ObjectId(self.id)
            collection.update_one({"_id": obj_id}, {"$set": data})

        return self

    @classmethod
    def _from_ref(cls: Type[T], ref: DBRef, unloaded: bool = True) -> T:
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
        if unloaded:
            model_fields_dict = dict(cls.model_fields.items())
            model_dict = {field: (value.annotation, value) for field, value in model_fields_dict.items()}
            for field_value in model_dict.values():
                field_value[1].default = None
            Model = create_model(cls.__name__, __base__=cls, **model_dict)
            instance = Model(False, **{})
            instance.__db_ref__ = ref
        else:
            instance = cls._get_by_filter({"_id": ref.id})
            if instance is None:
                raise ValueError(f"Can't get {cls.__name__} with id {ref.id}")

        return instance

    @classmethod
    def _objects(cls, filter: Optional[typing.Dict[str, Any]] = None) -> typing.Iterator[T]:
        """
        Get all models from database

        Args:
            filter: filter dict

        Returns:
            iterator with models
        """
        filter = filter or {}
        if filter.get("_id"):
            filter["_id"] = ObjectId(filter["_id"])

        for mongo_doc in cls.collection().find(filter or {}):
            yield cls._process_mongo_doc(mongo_doc)

    @classmethod
    def _get_by_filter(cls, filter: typing.Dict[str, Any], as_dict: bool = False) -> Optional[typing.Union[T, dict]]:
        """
        Get model by filter from database

        Args:
            filter: filter dict
            as_dict: if True, return dict instead of a model

        Returns:
            None if not found
            Model if as_dict is False
            Dict with db refs as models otherwise
        """
        if filter.get("_id"):
            filter["_id"] = ObjectId(filter["_id"])

        mongo_doc = cls.collection().find_one(filter)
        if not mongo_doc:
            return None

        return cls._process_mongo_doc(mongo_doc, as_dict=as_dict)

    def _get_ref_objects(self, mongo_doc: dict) -> typing.List[Optional[Base]]:
        """
        Get all ref objects from a model.

        Args:
            mongo_doc: dict with data from mongo

        Returns:
            list with ref objects
        """
        return [self._get_type_by_collection(ref.collection)._from_ref(ref) for ref in get_refs_from_data(mongo_doc)]

    @classmethod
    def _replace_refs_with_models(cls,
                                  mongo_doc: dict,
                                  model: typing.Literal['base', 'dict'] = 'base',
                                  unloaded: bool = True
                                  ) -> dict:
        """
        Replace DBRef with model data or None if not found

        Args:
            mongo_doc: dict with raw data from mongo db_refs should be bson.DBRef(collection: str, id: str)
            model: 'base' or 'dict'; if 'dict', return dict with DbRefModel
            unloaded: if True, models will be unloaded (by default), else they will be loaded from db

        Returns:
            dict with replaced refs
        """
        def replace(ref):
            if model == 'base':
                instance = cls._get_type_by_collection(ref.collection)._from_ref(ref, unloaded)
                instance.__is_loaded__ = not unloaded
                return instance
            else:
                return DbRefModel(**ref.as_doc()).model_dump()

        result = find_instance_in_data_and_replace(mongo_doc, DBRef, replace)

        return result

    @classmethod
    def _process_mongo_doc(cls, mongo_doc: Mapping[str, Any], as_dict: bool = False) -> typing.Union[T, dict]:
        """
        Process mongo doc and replace refs with models
        Args:
            mongo_doc: dict with raw data from mongo db_refs should be bson.DBRef(collection: str, id: str)
            as_dict: if True, return dict instead of a model

        Returns:
            dict or model
        """
        mongo_doc = dict(mongo_doc)
        data_with_models = cls._replace_refs_with_models(mongo_doc)
        if data_with_models.get("_id"):
            data_with_models["_id"] = str(data_with_models["_id"])
        return data_with_models if as_dict else cls(**data_with_models)

    def _model_dump(self, as_mongo_model: bool = False, **kwargs) -> dict[str, Any]:
        """
        Dump model to dict

        Args:
            as_mongo_model: if True, return dict with MongoModel
            **kwargs: kwargs for super().model_dump

        Returns:
            dict with model data
        """
        # for loading from db if model is not loaded
        self.__str__()
        self_dict = super().model_dump(**kwargs)
        if as_mongo_model:
            return self._MongoModel(**self_dict).model_dump_db(convert_to_db=False)
        return self_dict

    @classmethod
    def _init_mongo_model(cls):
        """
        Init MongoModel for a class

        Returns:
            None
        """
        cls._MongoModel = MongoModel.from_model(cls)

    @classmethod
    def _model_json_schema(cls, as_mongo_model: bool = False, by_alias: bool = False, **kwargs) -> dict[str, Any]:
        """
        Get json schema for a model

        Args:
            as_mongo_model: if True, return dict with MongoModel
            by_alias: if True, use alias names
            **kwargs: kwargs for super().model_json_schema

        Returns:
            dict with json schema
        """
        if as_mongo_model:
            cls._init_mongo_model()
            return cls._MongoModel.model_json_schema(**kwargs)
        else:
            return super(BasePydanticMongoModel, cls).model_json_schema(by_alias=by_alias, **kwargs)
