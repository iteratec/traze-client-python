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
        self.__game__:Game = None

    def join(self, game:Game):
        def on_update():
            nextAction = self.nextAction
            if nextAction: 
                self.steer(nextAction)
                      
        self.__game__ = game
        self.__player__:Player = Player(game, self._botName).join(on_update)
        print("Bot joined")

    def play(self, game:Game, count:int = 1):
        for i in range(1, count + 1):
            self.join(game)
            print("start game", i)

            # wait for death
            while(self.alive):
               time.sleep(0.5)
            print("end game", i)

        return self

    def die(self):
        self.__player__.die()

    @property
    def actions(self) -> set:
        print("actions at", self.x, self.y)
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
        if not self.__player__:
            return False
        return self.__player__.alive

    @property
    def x(self) -> int:
        if not self.__player__:
            return -1000000
        return self.__player__.x

    @property
    def y(self) -> int:
        if not self.__player__:
            return -1000000
        return self.__player__.y

    def valid(self, x:int, y:int) -> bool:
        if not self.alive:
            return False
        return self.__game__.grid.valid(x, y)

    # action darf None sein
    def steer(self, action:Action):
        if self.__player__ and action:
            print("  # steer", action, ", alive", self.alive)
            self.__player__.steer(action.name)
