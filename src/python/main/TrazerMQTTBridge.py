import json
import paho.mqtt.client as mqtt
from time import sleep

# r: traze/games
# [ { \"name\": \"dummyGame\", \"activePlayers\": 5 } ] 
# s: traze/{instanceName}/join
# r: traze/{instanceName}/player/{playerName}
# \"you\": { \"id\": 1337, \"name\": \"HansWurst\", \"secretUserToken\":\"secret\", \"position\": (15,3) }
# s: traze/{instanceName}/{playerId}/steer
# s: ...
# s: traze/{instanceName}/{playerId}/bail
#
# r: traze/{instanceName}/grid
# r: traze/{instanceName}/players
# r: traze/{instanceName}/ticker

# sent
TOPIC_PLAYER_JOIN = 'traze/+/join'
TOPIC_PLAYER_STEER = 'traze/+/+/steer'
TOPIC_PLAYER_BAIL = 'traze/+/+/bail'

# recieved
TOPIC_GAME_INFO = 'traze/games'
TOPIC_PLAYER_INFO = 'traze/+/player/+'
TOPIC_GRID = 'traze/+/grid'
TOPIC_PLAYERS = 'traze/+/players'
TOPIC_TICKER = 'traze/+/ticker'

def topic(topic: str, *args: str) -> str:
    return topic.replace('+', '%s') % (args)

def isMyMessage(message, myTopic: str, *args: str) -> bool:
    if (message.topic != topic(myTopic, *args)):
        print("... ignoring %s\n" % (message.topic))
        return False
    return True
    
class TrazerMQTTBridge:
    def __init__(self, playerName, host='localhost'):
        self._playerName = playerName
        self._gameName = ''
        self._games = {}
        self._player = {}
        
        self._client = mqtt.Client()
        self._client.on_connect = self.on_connect
        self._client.connect(host, 1883, 60)

        self._client.loop_start()

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code ", str(rc))

        def on_games(client, userdata, message):
            if (isMyMessage(message, TOPIC_GAME_INFO)):
                gameData = json.loads(message.payload.decode('utf-8'))
                print("update game data\n")
                for game in gameData:
                    self._games[game['name']] = game['activePlayers']

        def on_grid(client, userdata, message):
            if (isMyMessage(message, TOPIC_GRID, self._gameName)):
                print("on_grid: %s\n" % (message.payload))

        def on_players(client, userdata, message):
            if (isMyMessage(message, TOPIC_PLAYERS, self._gameName)):
                print("on_players: %s\n" % (message.payload))

        def on_ticker(client, userdata, message):
            if (isMyMessage(message, TOPIC_TICKER, self._gameName)):
                print("on_ticker: %s\n" % (message.payload))

        def on_player(client, userdata, message):
            if (isMyMessage(message, TOPIC_PLAYER_INFO, self._gameName, self._playerName)):
                playerData = json.loads('{' + message.payload.decode('utf-8') + '}')
                self._player = playerData['you']
                print("update player data\n")

        # set callbacks for game handling  
        client.subscribe('traze/#')
        client.message_callback_add(TOPIC_PLAYER_INFO, on_player)
        client.message_callback_add(TOPIC_GAME_INFO, on_games)
        client.message_callback_add(TOPIC_GRID, on_grid)
        client.message_callback_add(TOPIC_PLAYERS, on_players)
        client.message_callback_add(TOPIC_TICKER, on_ticker)

    def games(self):
        while not self._games:
            sleep(1)
        return self._games

    def join(self, gameName):
        if (gameName not in self.games()):
            print("Unknown game: '%s'!" % (gameName))
            return
        self._gameName = gameName
        
        playerData = json.dumps({ 'name' : self._playerName})
        self._client.publish(topic(TOPIC_PLAYER_JOIN, self._gameName), playerData)
        
        while not self._player:
            sleep(1)
        print("Welcome '%s' in game '%s'!\n" % (self._playerName, self._gameName))
        
    def bail(self):
        self._client.publish(topic(TOPIC_PLAYER_BAIL, self._gameName, str(self._player['id'])))
        self._client.loop_stop()
    
        self._gameName = ''
        self._games = {}
        self._player = {}
