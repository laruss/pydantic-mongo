# PydanticMongo

PydanticMongo is an ODM (Object-Document Mapper) for MongoDB, built upon the foundation of Pydantic and Flask-PyMongo. This allows you to leverage Pydantic's data validation and serialization capabilities, and seamlessly integrate it with MongoDB through Flask-PyMongo.

## Version

0.1.4.1

Changes:

- updated requirements versions
- added support for mongo indexes
- added support for a Literal type 

## Project Structure
```
root
|-- pydantic_mongo
|   |-- __init__.py
|   |-- base.py
|   |-- base_pm_model.py
|   |-- db_ref_model.py
|   |-- extensions.py
|   |-- helpers.py
|   |-- meta.py
|   |-- mongo_model.py
|   |-- pm_model.py
|-- tests
|   |-- integration
|   |-- unit
|-- readme.md
|-- requirements.txt
|-- setup.py
```

## Installation

To install `PydanticMongo`, you can clone the repository from GitHub or install it using pip:

```bash
pip install git+https://github.com/laruss/pydantic-mongo
```

*Note*: Ensure you are using Python 3.10 or newer.

## Usage

1. Initialization:

```python
from pydantic_mongo import PydanticMongo

pm = PydanticMongo()
pm.init_app(app)
```

2. Model creation:

```python
from pydantic_mongo import PydanticMongoModel as PmModel

class YourModel(PmModel):
    ...
```

2.1. Model creation with DBRefs as dicts with "collection", "database" and "id" keys:

```python
class YourModel(PmModel):
    nested_model: AnotherModel = AnotherModel()

data = {"nested_model": {"collection": "another_models", "database": "", "id": "id"}}
instance = YourModel.get_with_parse_db_refs(data)
```

2.2. Model creation with forward references:

```python
from __future__ import annotations
from typing import ForwardRef

class YourModel(PmModel):
    nested_model: ForwardRef("AnotherModel") = AnotherModel()
    nested_model_list: List[ForwardRef("AnotherModel")] = [AnotherModel()]
    nested_model_dict: Dict[str, ForwardRef("AnotherModel")] = {"key": AnotherModel()}

class AnotherModel(PmModel):
    name: str
    
YourModel.model_rebuild()

another_model = AnotherModel(name="name").save()
data = {"nested_model": another_model, "nested_model_list": [another_model]}
instance = YourModel(**data).save()

```

2.3 Model creation with field indexing:

```python
from pydantic_mongo import PydanticMongoModel as PmModel
from pymongo import IndexModel

class YourModel(PmModel):
    name: str
    age: int

    class _MongoConfig:
        indexes = [
            IndexModel([("name", 1)]),
            IndexModel([("age", 1)], unique=True)
        ]
        
YourModel(name="name", age=1).save()
YourModel(name="name", age=2).save()  # will raise PyMongoError
YourModel(name="name2", age=1).save() # will raise PyMongoError

```

3. Data operations:

- Retrieving by ID:

```python
instance = YourModel.get_by_id(your_id)
```

- Retrieving by filter:

```python
instance = YourModel.get_by_filter({"field": "value"})
```

- Saving data:

```python
instance.save()
```

- Deleting data:

```python
instance.delete()
```

- Retrieving objects by filter:

```python
objects = list(YourModel.objects({"field": "value"}))
```

## Key Features

- `get_by_id`: Retrieve an object by its ID.
  
- `get_by_filter`: Retrieve an object based on a specified filter.

- `save`: Save or update an object in the database.

- `delete`: Delete an object from the database.

- `objects`: Retrieve all objects that match a given filter.

- `model_dump`: Get a dictionary representation of the model.

- `model_json_schema`: Retrieve the JSON schema of the model.

- `db_ref`: Get a DBRef object for the model.

- `get_ref_objects`: Get the objects referenced to an object by a DBRef.

## Easy Document References

With PydanticMongo, creating references to other documents is straightforward. 

Example:

```python
from pydantic_mongo import PydanticMongoModel as PmModel

class YourAwesomeChild(PmModel):
    name: str

class YourAwesomeParent(PmModel):
    name: str
    children: List[YourAwesomeChild]

child = YourAwesomeChild(name="Victor")
child.save()

parent = YourAwesomeParent(name="Sam", children=[child])
parent.save()
print(parent)  # _id="id", name="Sam", children=[_id="id", name="Victor"]
```

In the database, these are represented by using bson.ObjectId linking to the `your_awesome_childs` collection.

`Note:` When a Document is referred as a db_ref, it won't be loaded until it is accessed. 
This is done to avoid circular references.

## Test Coverage

Made with [pytest-cov](https://pypi.org/project/pytest-cov/)

```bash
Name                              Stmts   Miss  Cover
-----------------------------------------------------
pydantic_mongo/__init__.py            2      0   100%
pydantic_mongo/base.py               63      2    97%
pydantic_mongo/base_pm_model.py     145      2    99%
pydantic_mongo/db_ref_model.py       11      0   100%
pydantic_mongo/extensions.py         28      1    96%
pydantic_mongo/helpers.py            45      0   100%
pydantic_mongo/meta.py               57      3    95%
pydantic_mongo/mongo_model.py        73      1    99%
pydantic_mongo/pm_model.py           42      0   100%
-----------------------------------------------------
TOTAL                               466      9    98%
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
To run the tests, use `pytest`:

```bash
pytest ./tests/unit
pytest ./tests/integration
```

`Note:` Integration tests require a running MongoDB instance.

## Conclusion

PydanticMongo offers a powerful toolset for working with MongoDB in Flask applications, integrating seamlessly with Pydantic for data validation and serialization. Use it to simplify and structure your database-interaction code.

## TODO

- [ ] Check for all the available pydantic methods
- [ ] Check for all the available mongo types
- [ ] Add support of various DBRef types
