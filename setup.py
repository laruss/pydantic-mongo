from setuptools import setup, find_packages

setup(
    name="pydantic-mongo",
    version="0.1.3",
    description="Pydantic models for MongoDB",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author="Konstantin Chistiakov",
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=[
        "pydantic~=2.3.0",
        "pymongo~=4.5.0",
        "Flask-PyMongo~=2.3.0"
    ]
)
