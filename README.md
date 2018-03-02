to simulate join():

mosquitto_pub.exe -h localhost -t traze/games -m "[ { \"name\": \"1\", \"activePlayers\": 2 } ] "
mosquitto_pub.exe -h localhost -t traze/1/player/HansWurst -m "{ \"id\": 2, \"name\": \"HansWurst\", \"secretUserToken\":\"secret\", \"position\": \"(15,3)\" }"
