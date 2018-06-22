import uuid
import functools
import paho.mqtt.client as mqtt
from typing import Callable

from .topic import MqttTopic

__all__ = [
    "TrazeMqttAdapter"
]

class TrazeMqttAdapter:

    def __init__(self, host='traze.iteratec.de', port=8883, transport='tcp'):
        def _on_connect(client, userdata, flags, rc):
            print("Connected to MQTT broker.")
            self.connected = True

        self.connected = False

        self.__client_id__:str = str(uuid.uuid4())
        self._client:mqtt.Client = mqtt.Client(client_id = self.__client_id__, transport=transport)
        self._client.on_connect = _on_connect
        self._client.tls_set_context()
        self._client.connect(host, port)
        self._client.loop_start()

    def on_game_info(self, on_game_info:Callable[[object], None]):
        self.__get_topic__('traze/games').subscribe(on_game_info)

    def on_player_info(self, game_name:str, on_player_info:Callable[[object], None]):
        self.__get_topic__('traze/+/player/+', game_name, self.__client_id__).subscribe(on_player_info)

    def on_grid(self, game_name:str, on_grid:Callable[[object], None]):
        self.__get_topic__('traze/+/grid', game_name).subscribe(on_grid)

    def on_players(self, game_name:str, on_players:Callable[[object], None]):
        self.__get_topic__('traze/+/players', game_name).subscribe(on_players)

    def on_ticker(self, game_name:str, on_ticker:Callable[[object], None]):
        self.__get_topic__('traze/+/ticker', game_name).subscribe(on_ticker)

    def publish_join(self, game_name:str, player_name:str):
        self.__get_topic__('traze/+/join', game_name).publish({ 'name' : player_name, 'mqttClientName' : self.__client_id__})

    def publish_steer(self, game_name:str, player_id:str, player_token:str, course:str):
        self.__get_topic__('traze/+/+/steer', game_name, player_id).publish({ 'course' : course, 'playerToken' : player_token})

    def publish_bail(self, game_name:str, player_id:str, player_token:str):
        self.__get_topic__('traze/+/+/bail', game_name, player_id).publish({'playerToken' : player_token})

    @functools.lru_cache()
    def __get_topic__(self, topic_name:str, *args: str) -> MqttTopic:    
        return MqttTopic(self._client, topic_name, *args)

    def destroy(self):
        self._client.loop_stop()
        self._client.disconnect()
