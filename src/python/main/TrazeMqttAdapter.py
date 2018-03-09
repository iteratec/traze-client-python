import json
import time
import uuid
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
        self._client = client

    def subscribe(self, *on_payload_funcs: Callable[[object], None]):
        def on_message(client, userdata, message: MQTTMessage):
            payload:object = json.loads(str(message.payload, 'utf-8'))
            for on_payload in on_payload_funcs:
                if on_payload:
                    on_payload(payload)

        # print("Subscribe at %s\n" % (self._name))
        self._client.subscribe(self._name)
        if on_payload_funcs:
            self._client.message_callback_add(self._name, on_message)
        return self

    def unsubscribe(self):
        self._client.message_callback_remove(self._name)
        self._client.unsubscribe(self._name)
        return self

    def publish(self, obj:object=None):
        self._client.publish(self._name, json.dumps(obj))

class TrazePlayer:
    def __init__(self, parent):
        self._parent = parent
        self._name = self._parent._name
        self._id = None
        self._secret = ''
        self._x, self._y = [-1, -1]
        self._direction = None
        self._frags = 0
        self._on_update = None
        self._bike = None
        self._tiles = None

    def __str__(self):
        return "TrazePlayer(name=%s,id=%s,x=%d,y=%d,dir=%s,frags=%d)" % (self._name, self._id, self._x, self._y, self._direction, self._frags)

    def __onJoin__(self, payload:object):
        self._id = payload['id']
        self._secret = payload['secretUserToken']
        self._x, self._y = payload['position']
        self._direction = None
        self._last = [self._x, self._y, self._direction]

        # workaround: always start the bot after joining
        self.steer('N')

    def __onGrid__(self, payload:object):
        self._bike = None
        self._tiles = payload['tiles']
        for bike in payload['bikes']:
            if (bike['playerId'] == self._id):
                self._bike = bike
                break

        if self._bike:
            self._x, self._y = self._bike['currentLocation']
            self._direction  = self._bike['direction']

            # workaround: guarantee this player was drawn on tiles
            for pos in self._bike['trail']:
                self._tiles[pos[1]][pos[0]] = self._id

            self.__callOnUpdate__()

    def __onPlayers__(self, payload:object):
        self._players = payload
        myPlayer = None
        for player in self._players:
            if (player['id'] == self._id):
                myPlayer = player
                break
                
        if myPlayer:
            self._frags = player['frags']

    def isAlive(self) -> bool:
        return self._id is not None

    def isMoving(self) -> bool:
        return self.isAlive() and self._direction is not None

    def subscribe(self, on_update:Callable[[None], None], wait = False):
        self._on_update = on_update
        if wait:
            while not self.isAlive():
                time.sleep(1)

    def steer(self, direction):
        if (self._x >= 0 and self._y >= 0):
            # print("# steer (%d,%d) -> %s (last: %s)" % (self._x, self._y, direction, self._direction))
            self._direction = direction
            self._parent.__steer__(direction)

    def bail(self):
        self._parent.__bail__()

        self._id = None
        self._secret = ''
        self._x, self._y = [-1, -1]
        self._direction = None
        self.__callOnUpdate__()

    def __callOnUpdate__(self):
        if self._on_update and self._last != [self._x, self._y, self._direction]:
            # print("call on_update() at ", [self._x, self._y, self._direction])
            self._on_update()
            self._last = [self._x, self._y, self._direction]

class TrazeMqttAdapter:    
    def __init__(self, clientName:str, host='traze.iteratec.de', port=8883, transport='tcp'):
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
        self._name = clientName
        self._clientId = str(uuid.uuid4())
        self._player:TrazePlayer = TrazePlayer(self)

        self._client = mqtt.Client(client_id = self._clientId, transport=transport)
        self._client.on_connect = on_connect
        self._client.tls_set_context()
        self._client.connect(host, port)

        self._client.loop_start()

    def games(self):
        return self._gameData

    def join(self, gameName:str, on_grid: Callable[[object], None] = None, on_players: Callable[[object], None] = None, on_ticker: Callable[[object], None] = None) -> TrazePlayer:
        if (gameName not in self.games()):
            print("Unknown game: '%s'!" % (gameName))
            return

        if self._player.isAlive():
            print("Player has already joined!")
            return
        
        def topic(name:str, *args: str) -> MqttTopic:
            return MqttTopic(self._client, name, gameName, *args)

        def on_join(payload:object):
            self.topicPlayerInfo.unsubscribe()

            # register listeners for player
            playerId = str(payload['id'])
            self.topicPlayerSteer = topic(TOPIC_PLAYER_STEER, playerId)
            self.topicPlayerBail = topic(TOPIC_PLAYER_BAIL, playerId)

            print("Welcome '%s' in game '%s'!\n" % (self._name, gameName))
            
        # register listeners for game
        self.topicGrid = topic(TOPIC_GRID).subscribe(self._player.__onGrid__, on_grid)
        self.topicPlayers = topic(TOPIC_PLAYERS).subscribe(self._player.__onPlayers__, on_players)
        self.topicTicker = topic(TOPIC_TICKER).subscribe(on_ticker)
        
        # send join 
        self.topicPlayerInfo = topic(TOPIC_PLAYER_INFO, self._clientId).subscribe(on_join, self._player.__onJoin__)
        topic(TOPIC_PLAYER_JOIN).publish({ 'name' : self._name, 'mqttClientName' : self._clientId})

        return self._player

    def __steer__(self, direction):
        if (self.topicPlayerSteer):
            self.topicPlayerSteer.publish({ 'course' : direction, 'playerToken' : self._player._secret })

    def __bail__(self):
        if (self.topicPlayerBail):
            self.topicPlayerBail.publish({ 'name' : self._name})
        if self.topicGrid: 
            self.topicGrid.unsubscribe()
        if self.topicPlayers: 
            self.topicPlayers.unsubscribe()
        if self.topicTicker: 
            self.topicTicker.unsubscribe()

        self.topicGrid = None
        self.topicPlayers = None
        self.topicTicker = None
        self.topicPlayerSteer = None
        self.topicPlayerBail = None

    def destroy(self):
        self._client.loop_stop()
