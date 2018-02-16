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
    
def topic(*subTopics: str) -> str:
	return "/".join(['traze', *subTopics])

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
            gameData = json.loads(message.payload.decode('utf-8'))
            print("update game data\n")
            for game in gameData:
                self._games[game['name']] = game['activePlayers']

        def on_grid(client, userdata, message):
            if (message.topic != topic(self._gameName, 'grid')):
                print("on_grid: ignoring %s\n" % (message.topic))
                return
            print("on_grid: %s\n" % (message.payload))

        def on_players(client, userdata, message):
            if (message.topic != topic(self._gameName, 'players')):
                print("on_players: ignoring %s\n" % (message.topic))
                return
            print("on_players: %s\n" % (message.payload))

        def on_ticker(client, userdata, message):
            if (message.topic != topic(self._gameName, 'ticker')):
                print("on_ticker: ignoring %s\n" % (message.topic))
                return
            print("on_ticker: %s\n" % (message.payload))

        def on_player(client, userdata, message):
            if (message.topic != topic(self._gameName, 'player', self._playerName)):
                print("on_player: ignoring %s\n" % (message.topic))
                return
            playerData = json.loads('{' + message.payload.decode('utf-8') + '}')
            self._player = playerData['you']
            print("update player data\n")
            
        # set callbacks for game handling  
        client.subscribe('traze/#')
        client.message_callback_add(topic('games'), on_games)
        client.message_callback_add(topic('+', 'grid'), on_grid)
        client.message_callback_add(topic('+', 'players'), on_players)
        client.message_callback_add(topic('+', 'ticker'), on_ticker)
        client.message_callback_add(topic('+', 'player', '+'), on_player)

    def games(self):
        while not self._games:
            sleep(1)
        return self._games

    def join(self, gameName):
        self._gameName = gameName
        
        playerData = json.dumps({ 'name' : self._playerName})
        self._client.publish(topic(self._gameName, 'join'), playerData)
        
        while not self._player:
            sleep(1)
        print("Welcome '%s' in game '%s'!\n" % (self._playerName, self._gameName))
        
    def bail(self):
        self._client.publish(topic(self._gameName, str(self._player['id']), 'bail'))
        self._client.loop_stop()
	
        self._gameName = ''
        self._games = {}
        self._player = {}
