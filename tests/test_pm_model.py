from __future__ import annotations

import unittest

from pydantic_mongo import PydanticMongoModel
from tests.base import BaseTestWithData


class Models:
    class TestUser(PydanticMongoModel):
        name: str

    class TestDocument(PydanticMongoModel):
        name: str
        user: Models.TestUser

    class DocumentCollection(PydanticMongoModel):
        __collection_name__ = "test_documents_collection"
        name: str
        users: list[Models.TestUser]
        users_map: dict[str, Models.TestUser]


class TestPydanticMongoModel(BaseTestWithData):
    def test_user_creation(self):
        user = Models.TestUser(name="test")
        user.save()

        users = list(Models.TestUser.objects())
        self.assertGreater(len(users), 3)
        self.assertEqual(users[-1].name, user.name)

    def test_user_get_by_uid(self):
        user = Models.TestUser(name="test")
        user.save()
        uid = user.id

        user = Models.TestUser.get_by_id(uid)
        self.assertIsNotNone(user)
        self.assertEqual(user.name, "test")

        user = Models.TestUser.get_by_id(str(uid))
        self.assertIsNotNone(user)
        self.assertEqual(user.name, "test")

        with self.assertRaises(Exception):
            Models.TestUser.get_by_id("123")

    def test_user_change_name(self):
        user = Models.TestUser(name="test")
        user.save()
        uid = user.id
        print(uid)
        user.name = "test2"
        user.save()
        user = Models.TestUser.get_by_id(uid)
        self.assertIsNotNone(user)
        self.assertEqual(user.name, "test2")

    def test_user_objects(self):
        [Models.TestUser(name="test") for _ in range(3)]
        users = list(Models.TestUser.objects())
        self.assertGreater(len(users), 2)

        for user in users:
            self.assertTrue(isinstance(user, Models.TestUser))

    def test_user_objects_with_filter(self):
        name = "test2"
        [Models.TestUser(name="test") for _ in range(3)]
        Models.TestUser(name=name).save()
        users = list(Models.TestUser.objects({"name": name}))
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].name, name)

    def test_get_model_dict(self):
        user = Models.TestUser(name="test")
        user.save()
        user_dict = user.model_dump()
        self.assertEqual(user_dict["name"], "test")
        self.assertEqual(user_dict["id"], user.id)

    def test_document_creation(self):
        user = Models.TestUser(name="test")
        user.save()
        document = Models.TestDocument(name="test", user=user)
        document.save()

        documents = list(Models.TestDocument.objects())
        self.assertGreater(len(documents), 3)
        document = documents[-1]
        self.assertEqual(document.name, document.name)
        self.assertEqual(document.user.name, user.name)

    def test_document_get_by_uid(self):
        user = Models.TestUser(name="test")
        user.save()
        document = Models.TestDocument(name="test", user=user)
        document.save()
        uid = document.id

        document = Models.TestDocument.get_by_id(uid)
        self.assertIsNotNone(document)
        self.assertEqual(document.name, "test")
        self.assertEqual(document.user.name, user.name)

        document = Models.TestDocument.get_by_id(str(uid))
        self.assertIsNotNone(document)
        self.assertEqual(document.name, "test")
        self.assertEqual(document.user.name, user.name)

        with self.assertRaises(Exception):
            Models.TestDocument.get_by_id("123")

    def test_document_change_name(self):
        user = Models.TestUser(name="test")
        user.save()
        document = Models.TestDocument(name="test", user=user)
        document.save()
        uid = document.id
        document.name = "test2"
        document.save()
        document = Models.TestDocument.get_by_id(uid)
        self.assertIsNotNone(document)
        self.assertEqual(document.name, "test2")
        self.assertEqual(document.user.name, user.name)

    def test_document_change_user(self):
        user = Models.TestUser(name="test")
        user.save()
        user2 = Models.TestUser(name="test2")
        user2.save()
        document = Models.TestDocument(name="test", user=user)
        document.save()
        uid = document.id
        document.user = user2
        document.save()
        document = Models.TestDocument.get_by_id(uid)
        self.assertIsNotNone(document)
        self.assertEqual(document.name, "test")
        self.assertEqual(document.user.name, user2.name)

    def test_document_objects(self):
        [Models.TestDocument(name="test", user=Models.TestUser(name="test")) for _ in range(3)]
        documents = list(Models.TestDocument.objects())
        self.assertGreater(len(documents), 2)

        for document in documents:
            self.assertTrue(isinstance(document, Models.TestDocument))

    def test_try_to_save_document_with_invalid_user(self):
        user = Models.TestUser(name="test")
        user.save()
        document = Models.TestDocument(name="test", user=user)
        document.save()
        uid = document.id
        user.delete()
        document.name = "test2"
        document.save()
        document = Models.TestDocument.get_by_id(uid)
        self.assertIsNotNone(document)
        self.assertEqual(document.name, "test2")
        self.assertIsNone(document.user)

    def test_not_saved_users_for_document(self):
        user = Models.TestUser(name="test")
        document = Models.TestDocument(name="test", user=user)
        with self.assertRaises(ValueError):
            document.save()

    def test_document_objects_with_filter(self):
        name = "test2"
        users = [Models.TestUser(name="test") for _ in range(3)]
        [user.save() for user in users]
        [Models.TestDocument(name="test", user=user).save() for user in users[:2]]
        Models.TestDocument(name=name, user=users[0]).save()
        documents = list(Models.TestDocument.objects({"name": name}))
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].name, name)

    def test_document_collection_creation(self):
        user = Models.TestUser(name="test")
        user.save()
        document = Models.DocumentCollection(name="test", users=[user], users_map={"test": user})
        document.save()

        documents = list(Models.DocumentCollection.objects())
        self.assertGreater(len(documents), 1)
        document = documents[-1]
        self.assertEqual(document.name, document.name)
        self.assertEqual(document.users[0].name, user.name)
        self.assertEqual(document.users_map["test"].name, user.name)

    def test_document_collection_get_by_uid(self):
        user = Models.TestUser(name="test")
        user.save()
        document = Models.DocumentCollection(name="test", users=[user], users_map={"test": user})
        document.save()
        uid = document.id

        document = Models.DocumentCollection.get_by_id(uid)
        self.assertIsNotNone(document)
        self.assertEqual(document.name, "test")
        self.assertEqual(document.users[0].name, user.name)
        self.assertEqual(document.users_map["test"].name, user.name)

        document = Models.DocumentCollection.get_by_id(str(uid))
        self.assertIsNotNone(document)
        self.assertEqual(document.name, "test")
        self.assertEqual(document.users[0].name, user.name)
        self.assertEqual(document.users_map["test"].name, user.name)

        with self.assertRaises(Exception):
            Models.DocumentCollection.get_by_id("123")

    def test_document_collection_change_name(self):
        user = Models.TestUser(name="test")
        user.save()
        document = Models.DocumentCollection(name="test", users=[user], users_map={"test": user})
        document.save()
        uid = document.id
        document.name = "test2"
        document.save()
        document = Models.DocumentCollection.get_by_id(uid)
        self.assertIsNotNone(document)
        self.assertEqual(document.name, "test2")
        self.assertEqual(document.users[0].name, user.name)
        self.assertEqual(document.users_map["test"].name, user.name)

    def test_document_collection_add_additional_user(self):
        user = Models.TestUser(name="test")
        user.save()
        user2 = Models.TestUser(name="test2")
        user2.save()
        document = Models.DocumentCollection(name="test", users=[user], users_map={"test": user})
        document.save()
        uid = document.id
        document.users.append(user2)
        document.save()
        document = Models.DocumentCollection.get_by_id(uid)
        self.assertIsNotNone(document)
        self.assertEqual(document.name, "test")
        self.assertEqual(document.users[0].name, user.name)
        self.assertEqual(document.users[1].name, user2.name)
        self.assertEqual(document.users_map["test"].name, user.name)

    def test_document_collection_change_user(self):
        user = Models.TestUser(name="test")
        user.save()
        user2 = Models.TestUser(name="test2")
        user2.save()
        document = Models.DocumentCollection(name="test", users=[user], users_map={"test": user})
        document.save()
        uid = document.id
        document.users[0] = user2
        document.save()
        document = Models.DocumentCollection.get_by_id(uid)
        self.assertIsNotNone(document)
        self.assertEqual(document.name, "test")
        self.assertEqual(document.users[0].name, user2.name)
        self.assertEqual(document.users_map["test"].name, user.name)


if __name__ == '__main__':
    unittest.main()
