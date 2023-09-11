import unittest

from bson import DBRef

from pydantic_mongo import PydanticMongo
from tests.helpers import create_app


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.context = self.app.test_request_context("/")
        self.context.push()

    def tearDown(self):
        self.context.pop()


class BaseTestWithData(BaseTest):
    def setUp(self):
        super().setUp()
        self.mongo = PydanticMongo()
        self.mongo.init_app(self.app)
        self.user_dict = {"name": "test_user"}
        self.user = self.mongo.db.test_users.insert_one(self.user_dict)
        self.user_final_dict = {"name": "test_user", "_id": self.user.inserted_id}
        self.user_final_dict_str = {"name": "test_user", "_id": str(self.user.inserted_id)}
        self.user2_dict = {"name": "test_user_2"}
        self.user2 = self.mongo.db.test_users.insert_one(self.user2_dict)
        self.user3_dict = {"name": "test_user_3"}
        self.user3 = self.mongo.db.test_users.insert_one(self.user3_dict)

        self.doc_dict = {"name": "test_document", "user": DBRef("test_users", str(self.user.inserted_id))}
        self.doc_dict_final = {"name": "test_document", "user": self.user_final_dict}
        self.doc_dict_final_str = {"name": "test_document", "user": self.user_final_dict_str}
        self.doc = self.mongo.db.test_documents.insert_one(self.doc_dict)
        self.doc2_dict = {"name": "test_document_2", "user": DBRef("test_users", str(self.user2.inserted_id))}
        self.doc2 = self.mongo.db.test_documents.insert_one(self.doc2_dict)
        self.doc3_dict = {"name": "test_document_3", "user": DBRef("test_users", str(self.user3.inserted_id))}
        self.doc3 = self.mongo.db.test_documents.insert_one(self.doc3_dict)

        self.doc_collection_dict = {"name": "test_documents_collection",
                                    "users": [DBRef("test_users", str(self.user.inserted_id))],
                                    "users_map": {"test": DBRef("test_users", str(self.user.inserted_id))}}
        self.doc_collection_dict_final = {"name": "test_documents_collection",
                                            "users": [self.user_final_dict],
                                            "users_map": {"test": self.user_final_dict}}
        self.doc_collection_dict_final_str = {"name": "test_documents_collection",
                                            "users": [self.user_final_dict_str],
                                            "users_map": {"test": self.user_final_dict_str}}
        self.doc_collection = self.doc_collection = self.mongo.db.test_documents_collection.insert_one(
            self.doc_collection_dict
        )

    def tearDown(self):
        super().tearDown()
        self.mongo.client.drop_database("test_db")
