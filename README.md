to simulate join():

mosquitto_pub.exe -h localhost -t traze/games -m "[ { \"name\": \"1\", \"activePlayers\": 2 } ] "
mosquitto_pub.exe -h localhost -t traze/1/player/HansWurst -m "{ \"id\": 2, \"name\": \"HansWurst\", \"secretUserToken\":\"secret\", \"position\": \"(15,3)\" }"

example:
import time
from TrazeMqttAdapter import TrazeMqttAdapter

def printGrid(payload):
    print(payload)

bridge = TrazerMQTTBridge("HansWurst")
bridge.join('1', on_grid=printGrid)
bridge.steer('N')

time.sleep(1)

bridge.bail()
bridge.destroy()
