from os import path
from setuptools import setup, find_packages


def read(fname):
    return open(path.join(path.dirname(__file__), fname)).read()


setup(
    name='traze-client',
    version='1.1',
    author="Danny Lade",
    author_email="dannylade@gmail.com",
    description=("A client for the simple tron-like multi client online game called 'Traze' which is using MQTT for communication."),
    license="LGPL",
    keywords="traze client game tron-like",
    url="https://github.com/iteratec/traze-client-python",
    location="https://github.com/iteratec/traze-client-python",
    long_description=read('README.md'),

    packages=find_packages('traze'),

    # project uses MQTT
    install_requires=[
        'python_version>="3.5"',
        'paho-mqtt==1.4.0',
    ],

    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Games/Entertainment :: Simulation",
        "Programming Language :: Python :: 3.5",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
    ],
)
