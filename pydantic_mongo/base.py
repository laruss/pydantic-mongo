import logging
import re
from typing import Optional, TypeVar, Type, List

from pydantic import BaseModel, Field
from pymongo import IndexModel
from pymongo.collection import Collection

from pydantic_mongo.extensions import PydanticMongo
from pydantic_mongo.meta import BaseMeta

T = TypeVar("T", bound="__Base")

logger = logging.getLogger(__name__)


class __Base(BaseModel, metaclass=BaseMeta):
    id: Optional[str] = Field(alias="_id", default=None)
    __collection_name__: Optional[str] = None
    _MongoConfig: Optional[type] = None

    class Config:
        extra = "forbid"

    @classmethod
    @property
    def collection_name(cls) -> str:
        if cls.__collection_name__ is not None:
            return cls.__collection_name__
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', cls.__name__).lower()
        return f"{name}s" if not name.endswith("s") else name

    @classmethod
    def _init_indexes(cls):
        if cls._MongoConfig is None:
            return
        cls_indexes: Optional[List[IndexModel]] = getattr(cls._MongoConfig, "indexes", None)

        if not cls_indexes:
            return

        if not isinstance(cls_indexes, list):
            raise TypeError(f"Indexes must be a list of dict, got {type(cls_indexes)}")

        collection = PydanticMongo().db[cls.collection_name]
        existing_indexes = [index['name'] for index in collection.list_indexes()]
        indexes_to_create = []
        for index in cls_indexes:
            if not isinstance(index, IndexModel):
                raise TypeError(f"Indexes must be a list of pymongo IndexModels, got {type(index)}")

            if index.document['name'] in existing_indexes:
                continue

            indexes_to_create.append(index)

        if indexes_to_create:
            collection.create_indexes(indexes_to_create)
            logger.info(f"Indexes {indexes_to_create} created for {cls.collection_name}")

    @classmethod
    @property
    def __mongo__(cls) -> PydanticMongo:
        engine = PydanticMongo()

        if engine.db is not None:
            cls._init_indexes()

        return engine

    @classmethod
    def _get_type_by_collection(cls: Type[T], col: str) -> Type[T]:
        mcls: BaseMeta = cls.__class__
        result = mcls.collection_type_map.get(col)
        if result is None:
            raise ValueError(f"Collection for {cls.__name__} is not found")
        return result

    @classmethod
    def collection(cls) -> Collection:
        if cls.__mongo__.db is None:
            raise ValueError("Make sure that PydanticMongo is initialized by calling PydanticMongo.init_app(app) first")
        return cls.__mongo__.db[cls.collection_name]
