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

class BotBase(Player):
    def __init__(self, game:'Game', name:str=None):
        super().__init__(game, name)

    def join(self):
        def on_update():
            nextAction = self.nextAction
            if nextAction: 
                self.steer(nextAction)

        super().join(on_update)
        print("Bot joined")

    def play(self, count:int = 1) -> 'BotBase':
        for i in range(1, count + 1):
            self.join()
            print("start game", i)

            # wait for death
            while(self.alive):
               time.sleep(0.5)
            print("end game", i)

        return self

    @property
    def actions(self) -> set:
        # print("# actions at", self.x, self.y)
        validActions:list = list()
        for action in list(Action):
            if self.valid(self.x + action.dX, self.y + action.dY):
                validActions.append(action)

        return validActions

    @property
    def nextAction(self) -> Action:
        return None

    def valid(self, x:int, y:int) -> bool:
        if not self.alive:
            return False
        return self.game.grid.valid(x, y)

    def steer(self, action:Action):
        # action darf None sein
        action and super().steer(action.name)
