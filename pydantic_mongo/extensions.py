from typing import Optional

from flask_pymongo import PyMongo
from pymongo import MongoClient
from pymongo.database import Database


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class PydanticMongo(metaclass=SingletonMeta):
    def __init__(self):
        self.mongo = None

    @property
    def db(self) -> Optional[Database]:
        return self.mongo.db if self.mongo else None

    @property
    def client(self) -> Optional[MongoClient]:
        return self.mongo.cx if self.mongo else None

    def init_app(self, app, uri=None, *args, **kwargs) -> None:
        self.mongo = PyMongo(app, uri, *args, **kwargs)
