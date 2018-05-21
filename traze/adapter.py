import uuid
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
        MqttTopic(self._client, 'traze/games').subscribe(on_game_info)

    def on_player_info(self, gameName:str, on_player_info:Callable[[object], None]):
        MqttTopic(self._client, 'traze/+/player/+', gameName, self.__client_id__).subscribe(on_player_info)

    def on_grid(self, gameName:str, on_grid:Callable[[object], None]):
        MqttTopic(self._client, 'traze/+/grid', gameName).subscribe(on_grid)

    def on_players(self, gameName:str, on_players:Callable[[object], None]):
        MqttTopic(self._client, 'traze/+/players', gameName).subscribe(on_players)

    def on_ticker(self, gameName:str, on_ticker:Callable[[object], None]):
        MqttTopic(self._client, 'traze/+/ticker', gameName).subscribe(on_ticker)

    def publish_join(self, gameName:str, playerName:str):
        MqttTopic(self._client, 'traze/+/join', gameName).publish({ 'name' : playerName, 'mqttClientName' : self.__client_id__})

    def publish_steer(self, gameName:str, playerId:str, playerToken:str, course:str):
        MqttTopic(self._client, 'traze/+/+/steer', gameName, playerId).publish({ 'course' : course, 'playerToken' : playerToken})

    def publish_bail(self, gameName:str, playerId:str, playerName:str):
        MqttTopic(self._client, 'traze/+/+/bail', gameName, playerId).publish({ 'name' : playerName})

    def destroy(self):
        self._client.loop_stop()
        self._client.disconnect()
