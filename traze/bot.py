import time
import random
from enum import Enum, unique

from .adapter import TrazeMqttAdapter
from .game import World, Game, Grid, Player

@unique
class Action(Enum):
    N = (0, 1)
    E = (1, 0)
    S = (0, -1)
    W = (-1, 0)

    def __init__(self, dX:int, dY:int):
        self.dX = dX
        self.dY = dY
        self.index = len(self.__class__.__members__)

    def __repr__(self):
        return "%s %d: %s" % (str(self), self.index, self.value)

class BotBase:
    def __init__(self, botName:str):
        self._botName:str = botName
        self.__player__:Player = None
        self.world:World = World() 
                      
    def join(self, game:Game=None):
        if not game:
            game = self.world.games[0]

        self.__player__ = game.join(self._botName)

    def play(self, count:int = 1):
        for i in range(1, count + 1):
            self.join()
            print("start game", i)

            # wait for death
            while(self.alive):
               time.sleep(0.5)
            print("end game", i)

        return self

    def die(self):
        self.__player__.die()

    def __onUpdate__(self):
        nextAction = self.nextAction
        if nextAction: 
            self.steer(nextAction)

    @property
    def actions(self) -> set:
        validActions:list = list()
        for action in list(Action):
            if self.valid(self.x + action.dX, self.y + action.dY):
                validActions.append(action)

        return validActions

    @property
    def nextAction(self) -> Action:
        return None

    # delegate 
    @property
    def alive(self) -> bool:
        return self.__player__ and self.__player__.isAlive()

    @property
    def x(self) -> int:
        if self.alive:
            return self.__player__._x
        return -1

    @property
    def y(self) -> int:
        if self.alive:
            return self.__player__._y
        return -1

    def valid(self, x:int, y:int) -> bool:
        if not self.alive:
            return False

        if (x < 0 or x > 61 or y < 0 or y > 61):
            return False

        for trail in self.__player__._trails.values():
            if ([x,y] in trail):
                return False

        return True

    def steer(self, action:Action):
        # print("  # steer", action, ", alive", self.alive)
        self.alive and action and self.__player__.steer(action.name)
