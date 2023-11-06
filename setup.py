from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="pydantic-mongo",
    version="0.1.4.3",
    description="Pydantic models for MongoDB",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Konstantin Chistiakov",
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=[
        "pydantic~=2.4.2",
        "pymongo~=4.6.0",
        "Flask-PyMongo~=2.3.0"
    ]
)
