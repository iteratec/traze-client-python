import time
import random
import numpy as np
import sys
sys.path.append("..")

from typing import Iterable
from traze.bot import Action, BotBase
from traze.game import World, Game

ALPHA = 1.0
GAMMA = 0.8

QValues = np.ndarray

class SimpleQBot(BotBase):
    ''' This bot does neither learn (ALPHA = 1.0) nor use a state, but look one step ahead.
    '''
    def __init__(self, game:'Game'):
        super().__init__(game)
        self._lastActions:QValues = np.zeros((len(Action)))

    def calculateActions(self, x:int, y:int, action:Action=None) -> QValues:
        ''' Use predefined values for simple selection 
        '''
        old_x = x
        old_y = y
        if action:
            x += action.dX
            y += action.dY

        actions:QValues = np.full((len(Action)), -20.0)
        if not self.valid(x, y):
            return actions

        for nextAction in list(Action):
            x2 = x + nextAction.dX
            y2 = y + nextAction.dY
            # going backward can never be valid
            if old_x == x2 and old_y == y2:
                continue

            # validate forward
            if self.valid(x2, y2):
                actions[nextAction.index] = 5

        print("    # (%d,%d) -> actions = %s" % (x, y, actions))
        return actions
        
    def selectNextAction(self, actions:QValues) -> Action:
        maximum:float = actions.max()
        return random.choice([a for a in list(Action) if actions[a.index] == maximum])

    @property
    def nextAction(self) -> Action:
        print("--- nextAction ---")
        currentActions:QValues = self.calculateActions(self.x, self.y)
        currentAction:Action = self.selectNextAction(self._lastActions)

        # add bonus for optimal current action
        currentActions[currentAction.index] += 1

        print("# current (%d,%d) -> actions = %s" % (self.x, self.y, currentActions))
        
        for action in list(Action):
            reward = currentActions[action.index]
            nextActions:QValues = self.calculateActions(self.x, self.y, action)
            q_1 = nextActions.max()

            currentActions[action.index] = reward + GAMMA * q_1

        nextAction = self.selectNextAction(currentActions)
        
        print("# next %s (%d,%d) -> actions = %s" % (nextAction, self.x+ nextAction.dX, self.y + nextAction.dY, currentActions))
        
        self._lastActions = currentActions

        return nextAction

if __name__ == "__main__":
    SimpleQBot(World().games[0]).play(1).die()
