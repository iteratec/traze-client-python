# -*- coding: utf-8 -*-
#
# Copyright 2018 The Traze Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
@author: Danny Lade
"""
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
        return "{} {}: {}".format(str(self), self.index, self.value)

    @classmethod
    def from_name(cls, name):
        for action in Action:
            if action.name == name:
                return action
        raise ValueError('{} is not a valid action name'.format(name))


class BotBase(Player, metaclass=ABCMeta):
    def __init__(self, game, name=None):
        def on_update():
            next_action = None
            actions = self.actions
            if actions:
                next_action = self.next_action(actions)
            if next_action:
                self.steer(next_action)

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
                    self.logger.warn("Timeout exceeded while waiting for join-response from server. This will be ignored.")  # noqa
                else:
                    raise e

        self.destroy()

    @property
    def actions(self):
        valid_actions = set()
        for action in list(Action):
            if self.valid(self.x + action.dX, self.y + action.dY):
                valid_actions.add(action)

        return tuple(valid_actions)

    @abstractmethod
    def next_action(self, actions):
        """
        Args:
            actions (Tuple[Action]): All possible actions.

        Returns:
            Action: Next action.
        """
        pass

    def steer(self, action):
        action and super().steer(action.name)
