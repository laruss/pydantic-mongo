# PydanticMongo

PydanticMongo is an ODM (Object-Document Mapper) for MongoDB, built upon the foundation of Pydantic and Flask-PyMongo. This allows you to leverage Pydantic's data validation and serialization capabilities, and seamlessly integrate it with MongoDB through Flask-PyMongo.

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
|   |-- mongo_model.py
|   |-- pm_model.py
|-- tests
|-- readme.md
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

## Conclusion

PydanticMongo offers a powerful toolset for working with MongoDB in Flask applications, integrating seamlessly with Pydantic for data validation and serialization. Use it to simplify and structure your database-interaction code.