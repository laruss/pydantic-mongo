import re
from typing import Optional

from pydantic import BaseModel, Field
from pymongo.collection import Collection

from pydantic_mongo.extensions import PydanticMongo


class __Base(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    __collection_name__: Optional[str] = None

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
    @property
    def __mongo__(cls) -> PydanticMongo:
        return PydanticMongo()

    @classmethod
    def collection(cls) -> Collection:
        if cls.__mongo__.db is None:
            raise ValueError("Make sure that PydanticMongo is initialized by calling PydanticMongo.init_app(app) first")
        return cls.__mongo__.db[cls.collection_name]
