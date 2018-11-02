import time
from abc import ABCMeta, abstractmethod
from enum import Enum, unique

from .client import Player, NotConnected


@unique
class Action(Enum):
    N = (0, 1)
    E = (1, 0)
    S = (0, -1)
    W = (-1, 0)

    def __init__(self, dX, dY):
        self.dX = dX
        self.dY = dY
        self.index = len(self.__class__.__members__)

    def __repr__(self):
        return "%s %d: %s" % (str(self), self.index, self.value)


class BotBase(Player, metaclass=ABCMeta):
    def __init__(self, game, name=None):
        def on_update():
            nextAction = self.next_action(self.actions)
            if nextAction:
                self.steer(nextAction)

        super().__init__(game, name, on_update)

    def play(self, count=1, suppress_server_timeout=False):
        for i in range(1, count + 1):
            try:
                self.join()
                self.logger.info("start game {}".format(i))

                # wait for death
                while(self.alive):
                    time.sleep(0.5)
                self.logger.info("end game {}".format(i))
            except NotConnected as e:
                if suppress_server_timeout:
                    self.logger.warn("Timeout exceeded while waiting for join-response from server. This will be ignored.")
                else:
                    raise e

        return self

    @property
    def actions(self):
        validActions = set()
        for action in list(Action):
            if self.valid(self.x + action.dX, self.y + action.dY):
                validActions.add(action)

        return validActions

    @abstractmethod
    def next_action(self, actions):
        """
        Args:
            actions (Set[Action]): All possible actions.

        Returns:
            Action: Next action.
        """
        pass

    def valid(self, x, y):
        if not self.alive:
            return False
        return self.game.grid.valid(x, y)

    def steer(self, action):
        # action darf None sein
        action and super().steer(action.name)
