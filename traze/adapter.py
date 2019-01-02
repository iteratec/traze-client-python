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
import uuid
import functools

import paho.mqtt.client as mqtt

from .log import setup_custom_logger
from .topic import MqttTopic

__all__ = [
    "TrazeMqttAdapter"
]


class TrazeMqttAdapter:

    def __init__(self, host='traze.iteratec.de', port=8883, transport='tcp'):
        self.logger = setup_custom_logger(name=type(self).__name__)

        def _on_connect(client, userdata, flags, rc):
            self.logger.info("Connected the MQTT broker.")

        def _on_disconnect(client, userdata, rc):
            self.logger.info("Disconnected the MQTT broker.")
            self._client.loop_stop()

        self.__client_id__ = str(uuid.uuid4())
        self._client = mqtt.Client(client_id=self.__client_id__, transport=transport)  # noqa
        self._client.on_connect = _on_connect
        self._client.on_disconnect = _on_disconnect

        self._client.tls_set_context()
        self._client.connect(host, port)
        self._client.loop_start()

    def on_heartbeat(self, game_name, on_heartbeat):
        # there is no heartbeat from server but the grid-event is a good base
        self.__get_topic__('traze/+/grid', game_name).subscribe(on_heartbeat)

    def on_game_info(self, on_game_info):
        self.__get_topic__('traze/games').subscribe(on_game_info)

    def on_player_info(self, game_name, on_player_info):
        self.__get_topic__('traze/+/player/+', game_name, self.__client_id__).subscribe(on_player_info)  # noqa

    def on_grid(self, game_name, on_grid):
        self.__get_topic__('traze/+/grid', game_name).subscribe(on_grid)

    def on_players(self, game_name, on_players):
        self.__get_topic__('traze/+/players', game_name).subscribe(on_players)

    def on_ticker(self, game_name, on_ticker):
        self.__get_topic__('traze/+/ticker', game_name).subscribe(on_ticker)

    def publish_join(self, game_name, player_name):
        self.__get_topic__('traze/+/join', game_name).publish({'name': player_name, 'mqttClientName': self.__client_id__})  # noqa

    def publish_steer(self, game_name, player_id, player_token, course):
        self.__get_topic__('traze/+/+/steer', game_name, player_id).publish({'course': course, 'playerToken': player_token})  # noqa

    def publish_bail(self, game_name, player_id, player_token):
        self.__get_topic__('traze/+/+/bail', game_name, player_id).publish({'playerToken': player_token})  # noqa

    def disconnect(self):
        self._client.disconnect()

    @functools.lru_cache()
    def __get_topic__(self, topic_name, *args):
        return MqttTopic(self._client, topic_name, *args)
