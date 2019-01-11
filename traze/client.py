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
import copy
from abc import ABCMeta, abstractmethod

from .log import setup_custom_logger
from .adapter import TrazeMqttAdapter


class NotConnected(TimeoutError):
    pass


class TileOutOfBoundsException(Exception):
    pass


class PlayerNotJoinedException(Exception):
    pass


class Base:
    def __init__(self, parent=None, name=None):
        self.logger = setup_custom_logger(self)

        self.__adapter__ = None
        self._parent = parent
        self._name = name or self.__class__.__name__

    @property
    def name(self):
        return self._name

    @property
    def adapter(self):
        if self.__adapter__:
            return self.__adapter__
        if self._parent:
            return self._parent.adapter
        return None


class Grid(Base, metaclass=ABCMeta):
    def __init__(self, game):
        super().__init__(game)
        self.width = 0
        self.height = 0
        self.tiles = [[]]
        self.bike_positions = {}

    def update_grid(self, payload):
        self.width = payload['width']
        self.height = payload['height']
        self.tiles = copy.deepcopy(payload['tiles'])
        for bike in payload['bikes']:
            self.bike_positions[bike['playerId']] = tuple(bike['currentLocation'])  # noqa

    @property
    def game(self):
        return self._parent

    def __getitem__(self, coordinates):
        x, y = coordinates
        if (x < 0 or x >= self.width or y < 0 or y >= self.height):
            raise TileOutOfBoundsException
        return self.tiles[x][y]


class Player(Base, metaclass=ABCMeta):
    def __init__(self, game, name):
        super().__init__(game, name=name)
        self.__reset__()

        def on_join(payload):
            self._id = payload['id']
            self._secret = payload['secretUserToken']
            self._x, self._y = payload['position']

            self.logger.info("Welcome '{}' ({}) at {}!\n".format(self.name, self._id, (self._x, self._y)))  # noqa
            self._joined = True

        def on_grid(payload):
            if not self._joined:
                return

            self.game.grid.update_grid(payload)

            if self.last_course:
                self._alive = True
                self._x, self._y = self.game.grid.bike_positions.get(self._id, (self._x, self._y))

            self.logger.debug("on_grid: position={}".format((self._x, self._y)))
            self.on_update()

        def on_ticker(payload):
            if not self.alive:
                return

            # not my cup of tea
            if self._id not in (payload['casualty'], payload['fragger']):
                return

            self.logger.debug("ticker: {}".format(payload))

            if payload['casualty'] == self._id or payload['type'] == 'collision':
                self._alive = False
                self._joined = False
                self.on_dead()

                self.__reset__()

        self.adapter.on_player_info(self.game.name, on_join)
        self.adapter.on_ticker(self.game.name, on_ticker)
        self.adapter.on_grid(self.game.name, on_grid)

    def __reset__(self):
        self._id = None
        self._secret = None
        self._alive = False
        self._joined = False
        self.last_course = None
        self._x, self._y = [-1, -1]

    def join(self):
        if self.alive:
            self.logger.info("Player '{}' is already alive!".format(self.name))
            return

        # send join and wait for player
        self.adapter.publish_join(self.game.name, self.name)
        for _ in range(30):
            if self.alive:
                return self
            time.sleep(0.5)
        raise NotConnected()

    @abstractmethod
    def on_update(self):
        pass

    @abstractmethod
    def on_dead(self):
        pass

    @property
    def game(self):
        return self._parent

    @property
    def alive(self):
        return self._alive

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    def valid(self, x, y):
        try:
            return (self.game.grid[x, y] == 0)
        except TileOutOfBoundsException:
            return False

    def steer(self, course):
        if course == self.last_course:
            return

        self.logger.debug("steer {}".format(course))

        self.last_course = course
        self.adapter.publish_steer(self.game.name, self._id, self._secret, course)  # noqa

    def bail(self):
        self.logger.debug("bail: {} ({})".format(self.game.name, self._id))

        self.adapter.publish_bail(self.game.name, self._id, self._secret)
        self.__reset__()

    def destroy(self):
        if self._id and self._secret:
            self.bail()

        self.adapter.disconnect()

    def __str__(self):
        return "{}(name={}, id={}, x={}, y={})".format(self.__class__.__name__, self.name, self._id, self._x, self._y)  # noqa


class Game(Base, metaclass=ABCMeta):
    def __init__(self, world, name):
        super().__init__(world, name=name)
        self._grid = Grid(self)

    @property
    def world(self):
        return self._parent

    @property
    def grid(self):
        return self._grid


class World(Base):
    def __init__(self, adapter=None):
        super().__init__()

        self.__adapter__ = adapter if adapter else TrazeMqttAdapter()
        self.__games__ = dict()

        def on_game_info(payload):
            for game in payload:
                name = game['name']
                if name not in self.__games__:
                    self.__games__[name] = Game(self, name)

        self.adapter.on_game_info(on_game_info)

    @property
    def games(self):
        for _ in range(30):
            if self.__games__:
                return tuple(self.__games__.values())
            time.sleep(0.5)
        raise NotConnected()
