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
import json
import functools


__all__ = [
    "MqttTopic"
]


class MqttTopic:
    @classmethod
    @functools.lru_cache()
    def name(cls, topic_name, *args):
        if not args:
            return topic_name
        return topic_name.replace('+', '%s') % (args)

    def __init__(self, client, name, *args):
        self._client = client
        self._name = MqttTopic.name(name, *args)
        self.functions = set()

    def subscribe(self, on_payload_func):
        def on_message(client, userdata, message):
            payload = json.loads(str(message.payload, 'utf-8'))
            for on_payload in self.functions:
                on_payload(payload)

        if not self.functions:
            self._client.subscribe(self._name)
            self._client.message_callback_add(self._name, on_message)

        # TODO - this check does not work if the function is defined anonymously  # noqa
        if on_payload_func not in self.functions:
            self.functions.add(on_payload_func)

    def publish(self, obj=None):
        self._client.publish(self._name, json.dumps(obj))
