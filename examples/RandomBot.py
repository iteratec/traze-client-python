import time
import random
import sys
sys.path.append("..")

from typing import List
from traze.bot import Action, BotBase
from traze.game import World, Game

class RandomBot(BotBase):
    def __init__(self, game:'Game'):
        super().__init__(game)
        self._lastAction:Action = None
        
    def next_action(self, actions:List[Action]) -> Action:
        if not actions:
            return None

        # prefer the same action as far as possible
        if self._lastAction not in actions:
            self._lastAction = random.choice(tuple(actions))
        return self._lastAction

if __name__ == "__main__":
    RandomBot(World().games[0]).play(1).die()
