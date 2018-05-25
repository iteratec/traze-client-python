import time
import random
import sys
sys.path.append("..")

from traze.bot import Action, BotBase
from traze.game import World, Game

class RandomBot(BotBase):
    def __init__(self, game:'Game'):
        super().__init__(game)
        self._lastAction:Action = None
        
    @property
    def nextAction(self) -> Action:
        actions:list = self.actions
        # print("# actions", [action.name for action in actions])
        if not actions:
            return None

        # prefer the same action as far as possible
        if self._lastAction not in actions:
            self._lastAction = random.choice(tuple(actions))
        return self._lastAction

if __name__ == "__main__":
    RandomBot(World().games[0]).play(1).die()
