from __future__ import annotations

from pydantic import BaseModel, create_model
from typing import Any, Optional, Type

from pydantic_mongo.base import __Base as Base


class DbRefModel(BaseModel):
    collection: str
    id: Any
    database: Optional[str] = None

    @classmethod
    def from_model(cls, field_type: Type[Base]) -> Type[DbRefModel]:
        return create_model(
            'DbRefModel',
            collection=(str, field_type.collection_name),
            id=(Any, ...),
            database=(str, None),
            __base__=DbRefModel
        )
