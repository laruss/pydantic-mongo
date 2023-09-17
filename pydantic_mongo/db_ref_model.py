from __future__ import annotations

from pydantic import BaseModel, create_model, Field
from typing import Any, Optional, Type

from pydantic_mongo.base import __Base as Base


class DbRefModel(BaseModel):
    collection: str
    id: Any
    database: str = Field(default="")

    @classmethod
    def from_model(cls, field_type: Type[Base]) -> Type[DbRefModel]:
        return create_model(
            'DbRefModel',
            collection=(str, field_type.collection_name),
            id=(Any, ...),
            database=(str, ""),
            __base__=DbRefModel
        )
