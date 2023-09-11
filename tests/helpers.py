import flask

from tests.config import TestConfig


def create_app():
    app = flask.Flask(__name__)
    app.config.from_object(TestConfig)
    return app
