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
import logging

__all__ = [
    "setup_custom_logger"
]

# make RootLogger quiet
ROOT_LOGGER = logging.getLogger()
ROOT_LOGGER.handlers = []


def setup_custom_logger(obj, level=logging.INFO):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(name)s - %(message)s')  # noqa

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(type(obj).__name__)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger
