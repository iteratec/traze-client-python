import time
import random
from traze import *
 
class RandomBot:
    def __init__(self):
        self._mqttAdapter = TrazeMqttAdapter("HansWurst")
        self._gameName, playerCount = next(iter(self._mqttAdapter.games().items()))
        self._lastDir = 'N'
        
    def __onUpdate__(self, player):
        directions = {'N' : (0, 1), 'S' : (0, -1), 'E' : (1, 0), 'W' : (-1, 0)}
        invalidDirs = set()
        for dir, delta  in directions.items():
            dX, dY = delta
            x, y = player._x + dX, player._y + dY
            if (x < 0 or x > 61 or y < 0 or y > 61):
                invalidDirs.add(dir)
                continue

            for player_id, trail in player._trails.items():
                if ([x,y] in trail):
                    invalidDirs.add(dir)

        validDirs = set(directions.keys()).difference(invalidDirs)
        if validDirs: 
            if self._lastDir not in validDirs:
                self._lastDir = random.choice(tuple(validDirs))

            dX, dY = directions[self._lastDir]
            x, y = player._x + dX, player._y + dY
            # print("steer from", player._x, player._y, 'to', x, y, '(' + self._lastDir + ')')
            player.steer(self._lastDir)
        else:
            player.bail()
            
    def play(self, count:int = 1):
        for i in range(1, count + 1):
            self._player = self._mqttAdapter.join(self._gameName)
            self._player.subscribe(self.__onUpdate__, wait = True)
            print("start game", i)

            # wait for death
            while(self._player.isAlive()):
               time.sleep(0.5)
            print("end game", i)

    def die(self):
        self._player.die()
