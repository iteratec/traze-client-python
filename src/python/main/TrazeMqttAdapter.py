import json
import time
import paho.mqtt.client as mqtt

from paho.mqtt.client import MQTTMessage
from typing import Callable

# sent
TOPIC_PLAYER_JOIN = 'traze/+/join'
TOPIC_PLAYER_STEER = 'traze/+/+/steer'
TOPIC_PLAYER_BAIL = 'traze/+/+/bail'

# recieved 
TOPIC_GAME_INFO = 'traze/games'
TOPIC_GRID = 'traze/+/grid'
TOPIC_PLAYERS = 'traze/+/players'
TOPIC_TICKER = 'traze/+/ticker'
TOPIC_PLAYER_INFO = 'traze/+/player/+'

class MqttTopic:
    def __init__(self, client: mqtt.Client, name:str, *args: str):
        self._name = name.replace('+', '%s') % (args)
        self._message = None
        self._client = client

    def subscribe(self, on_payload: Callable[[object], None] = None):
        def on_message(client, userdata, message: MQTTMessage):
            self._message = message
            if (on_payload):
                on_payload(json.loads(str(self._message.payload, 'utf-8')))

        self._client.subscribe(self._name)
        self._client.message_callback_add(self._name, on_message)
        return self

    def unsubscribe(self):
        self._client.message_callback_remove(self._name)
        self._client.unsubscribe(self._name)
        return self

    def publish(self, obj:object=None):
        self._client.publish(self._name, json.dumps(obj))
    
class TrazeMqttAdapter:    
    def __init__(self, playerName, host='traze.iteratec.de', port=1883):
        def on_gameInfo(payload:object):
            for game in payload:
                self._gameData[game['name']] = game['activePlayers']

        def on_connect(client, userdata, flags, rc):
            print("Connected MQTT broker.")
            self.topicGameInfo = MqttTopic(client, TOPIC_GAME_INFO).subscribe(on_gameInfo)

        self.topicGrid = None
        self.topicPlayers = None
        self.topicTicker = None
        self.topicPlayerSteer = None
        self.topicPlayerBail = None

        self._gameData = {} 
        self._player = {"name" : playerName}

        self._client = mqtt.Client(client_id = playerName)
        self._client.on_connect = on_connect
        self._client.connect(host, port, 60)

        self._client.loop_start()

    def games(self):
        return self._gameData

    def join(self, gameName:str, on_grid: Callable[[object], None] = None, on_players: Callable[[object], None] = None, on_ticker: Callable[[object], None] = None):
        # TODO
        # if (gameName not in self.games()):
        #    print("Unknown game: '%s'!" % (gameName))
        #    return
        
        def topic(name:str, *args: str) -> MqttTopic:
            return MqttTopic(self._client, name, gameName, *args)

        def on_playerInfo(payload:object):
            self.topicPlayerInfo.unsubscribe()
            self._player = payload

            # register listeners for player
            playerId = str(self._player['id'])
            self.topicPlayerSteer = topic(TOPIC_PLAYER_STEER, playerId)
            self.topicPlayerBail = topic(TOPIC_PLAYER_BAIL, playerId)

            print("Welcome '%s' in game '%s'!\n" % (self._player['name'], gameName))

        # register listeners for game
        self.topicGrid = topic(TOPIC_GRID).subscribe(on_grid)
        self.topicPlayers = topic(TOPIC_PLAYERS).subscribe(on_players)
        self.topicTicker = topic(TOPIC_TICKER).subscribe(on_ticker)
        
        # send join 
        self.topicPlayerInfo = topic(TOPIC_PLAYER_INFO, self._player['name']).subscribe(on_playerInfo)
        topic(TOPIC_PLAYER_JOIN).publish({ 'name' : self._player['name']})

    def steer(self, direction):
        if (self.topicPlayerSteer):
            self.topicPlayerSteer.publish({ 'course' : direction, 'playerToken' : self._player.secretUserToken })

    def bail(self):
        if (self.topicPlayerBail):
            self.topicGrid.unsubscribe()
            self.topicPlayers.unsubscribe()
            self.topicTicker.unsubscribe()

            self.topicPlayerBail.publish({ 'name' : self._player['name']})

        self.topicGrid = None
        self.topicPlayers = None
        self.topicTicker = None
        self.topicPlayerSteer = None
        self.topicPlayerBail = None
        self._player = None

    def destroy(self):
        self._client.loop_stop()
