import pytest

from pydantic_mongo import PydanticMongo
from tests.helpers import create_app


@pytest.fixture(scope="session")
def app():
    app = create_app()
    context = app.test_request_context("/")
    context.push()

    yield app

    context.pop()


@pytest.fixture(scope="function")
def mongo(app):
    mongo = PydanticMongo()
    mongo.init_app(app)

    yield mongo

    mongo.client.drop_database("test_db")
