import random

from traze.bot import BotBase
from traze.client import World


class RandomBot(BotBase):
    def __init__(self, game):
        """
        Args:
            game (Game): The game object.

        Returns:
            ---
        """
        super().__init__(game)
        self._lastAction = None

    def next_action(self, actions):
        """
        Args:
            actions (Set[Action]): All possible actions.

        Returns:
            Action: Next action.
        """
        if not actions:
            return None

        # prefer the same action as far as possible
        if self._lastAction not in actions:
            self._lastAction = random.choice(tuple(actions))
        return self._lastAction


if __name__ == "__main__":
    RandomBot(World().games[0]).play(3)
