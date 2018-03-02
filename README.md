to simulate join():

mosquitto_pub.exe -h localhost -t traze/games -m "[ { \"name\": \"1\", \"activePlayers\": 2 } ] "
mosquitto_pub.exe -h localhost -t traze/1/player/HansWurst -m "{ \"id\": 2, \"name\": \"HansWurst\", \"secretUserToken\":\"secret\", \"position\": \"(15,3)\" }"

example
from TrazerMQTTBridge import TrazerMQTTBridge

bridge = TrazerMQTTBridge("HansWurst")
bridge.join('1')
bridge.steer('N')

print(bridge.grid())

bridge.bail()
bridge.destroy()
