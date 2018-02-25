import json
import paho.mqtt.client as mqtt

from time import sleep
from paho.mqtt.client import MQTTMessage

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
        self._lastMessage = None
        self._client = client

    def subscribe(self):
        def on_message(client, userdata, message: MQTTMessage):
            self._message = message

        self._client.subscribe(self._name)
        self._client.message_callback_add(self._name, on_message)
        return self

    def unsubscribe(self):
        self._client.message_callback_remove(self._name)
        self._client.unsubscribe(self._name)
        return self

    def payload(self) -> object:
        return json.loads(self.rawPayload())

    def rawPayload(self) -> bytes:
        while self._lastMessage == self._message:
            sleep(1)
        self._lastMessage = self._message
        return self._message.payload

    def publish(self, obj:object=None):
        self._client.publish(self._name, json.dumps(obj))
    
class TrazerMQTTBridge:    
    def __init__(self, playerName, host='localhost', port=1883):
        def on_connect(client, userdata, flags, rc):
            print("Connected MQTT broker.")
            self.topicGameInfo = MqttTopic(client, TOPIC_GAME_INFO).subscribe()

        self._playerName = playerName
        self._player = {}
        
        self._client = mqtt.Client()
        self._client.on_connect = on_connect
        self._client.connect(host, port, 60)

        self._client.loop_start()

    def games(self):
        gameData = {} 
        for game in self.topicGameInfo.payload():
            gameData[game['name']] = game['activePlayers']

        print("updated game data: %s\n" % (gameData))
        return gameData

    def grid(self):
        if (self.topicGrid):
            return self.topicGrid.payload()
        return None
        
    def players(self):
        if (self.topicPlayers):
            return self.topicPlayers.payload()
        return None
        
    def ticker(self):
        if (self.topicTicker):
            return self.topicTicker.payload()
        return None

    def join(self, gameName:str):
        if (gameName not in self.games()):
            print("Unknown game: '%s'!" % (gameName))
            return
        
        def topic(name:str, *args: str) -> MqttTopic:
            return MqttTopic(self._client, name, gameName, *args)

        # send join
        topic(TOPIC_PLAYER_JOIN).publish({ 'name' : self._playerName})

        # register listeners for game
        self.topicPlayerInfo = topic(TOPIC_PLAYER_INFO, self._playerName).subscribe()
        self.topicGrid = topic(TOPIC_GRID).subscribe()
        self.topicPlayers = topic(TOPIC_PLAYERS).subscribe()
        self.topicTicker = topic(TOPIC_TICKER).subscribe()
        
        # recieve player data
        # TODO: workaround for "self.topicPlayerInfo.payload()" - JSON is broken        
        rawPayload = self.topicPlayerInfo.rawPayload()
        playerData = json.loads('{' + rawPayload.decode('utf-8') + '}')
        self._player = playerData['you']

        # register listeners for player
        playerId = str(self._player['id'])
        self.topicPlayerSteer = topic(TOPIC_PLAYER_STEER, playerId)
        self.topicPlayerBail = topic(TOPIC_PLAYER_BAIL, playerId)

        print("Welcome '%s' in game '%s'!\n" % (self._playerName, gameName))

    def steer(self, direction):
        raise RuntimeWarning('Not implemented yet.')

    def bail(self):
        if (self._player):
            self.topicPlayerInfo.unsubscribe()
            self.topicGrid.unsubscribe()
            self.topicPlayers.unsubscribe()
            self.topicTicker.unsubscribe()

            self.topicPlayerBail.publish({ 'name' : self._playerName})

        self._player = None

    def destroy(self):
        self._client.loop_stop()
