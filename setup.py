# -*- coding: utf-8 -*-
#
# Copyright 2018 The Traze Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
@author: Danny Lade
"""
from os import path
from setuptools import setup, find_packages


def __readme__():
    return open(path.join(path.dirname(__file__), 'README.md')).read()


setup(
    name='traze-client',
    version='1.3.1',
    author="Danny Lade",
    author_email="dannylade@gmail.com",
    description=("A client for the simple tron-like multi client online game called 'Traze' which is using MQTT for communication."),  # noqa
    license='GPLv3',
    keywords="traze client game tron-like",
    url="https://traze.iteratec.de/",
    project_urls={
        "Sources": "https://github.com/iteratec/traze-client-python",
	"Example Bots": "https://github.com/iteratec/traze-bots-python/tree/master",
    },
    long_description=__readme__(),
    long_description_content_type='text/markdown',

    packages=find_packages('traze'),

    install_requires=[
        'python_version>="3.5"',
        'paho-mqtt==1.4.0',
    ],

    classifiers=[
        # Development Status :: 1 - Planning
        # Development Status :: 2 - Pre-Alpha
        # Development Status :: 3 - Alpha
        # Development Status :: 4 - Beta
        # Development Status :: 5 - Production/Stable
        # Development Status :: 6 - Mature
        # Development Status :: 7 - Inactive
        "Development Status :: 5 - Production/Stable",
        "Topic :: Games/Entertainment :: Simulation",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
