to simulate join():

mosquitto_pub.exe -h localhost -t traze/games -m "[ { \"name\": \"dummyGame\", \"activePlayers\": 5 } ] "
mosquitto_pub.exe -h localhost -t traze/dummyGame/player/HansWurst -m "\"you\": { \"id\": 1337, \"name\": \"HansWurst\", \"secretUserToken\":\"secret\", \"position\": \"(15,3)\" }"
