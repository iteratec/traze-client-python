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
from .log import setup_custom_logger

from .adapter import TrazeMqttAdapter


class NotConnected(TimeoutError):
    pass


class Base:
    def __init__(self, parent=None, name=None):
        self.logger = setup_custom_logger(name=type(self).__name__)

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


class Grid(Base):
    def __init__(self, game):
        super().__init__(game)
        self.width = 0
        self.height = 0
        self.tiles = [[]]
        self.bike_positions = {}

        def on_grid(payload):
            self.width = payload['width']
            self.height = payload['height']
            self.tiles = copy.deepcopy(payload['tiles'])
            for bike in payload['bikes']:
                self.bike_positions[bike['playerId']] = tuple(bike['currentLocation'])  # noqa

        self.adapter.on_grid(self.game.name, on_grid)

    @property
    def game(self):
        return self._parent

    def valid(self, x, y):
        if (x < 0 or x >= self.width or y < 0 or y >= self.height):
            return False
        return self.tiles[x][y] == 0


class Player(Base):
    def __init__(self, game, name, on_update):
        super().__init__(game, name=name)
        self.__reset__()

        def on_join(payload):
            self._id = payload['id']
            self._secret = payload['secretUserToken']
            self._x, self._y = payload['position']

            self.logger.info("Welcome '{}' ({}) at {}!\n".format(self.name, self._id, (self._x, self._y)))  # noqa
            update_alive(True)  # very first call, if born

        def on_ticker(payload):
            if not self.alive:
                return

            # not my cup of tea
            if self._id not in (payload['casualty'], payload['fragger']):
                return

            self.logger.debug("ticker: {}".format(payload))

            if payload['casualty'] == self._id or payload['type'] == 'collision':  # noqa
                update_alive(False)  # very last call, if died

        def on_heartbeat(payload):
            if not self.alive:
                return

            bike_position = self.game.grid.bike_positions.get(self._id)
            if bike_position:
                self._x, self._y = bike_position
                on_update()  # call if heartbeat

        def update_alive(alive):
            self._alive = alive
            on_update()

            if not alive:
                self.__reset__()

        self.adapter.on_player_info(self.game.name, on_join)
        self.adapter.on_ticker(self.game.name, on_ticker)
        self.adapter.on_heartbeat(self.game.name, on_heartbeat)

    def __reset__(self):
        self._id = None
        self._secret = None
        self._alive = False
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

    @property
    def game(self):
        return self._parent

    @property
    def alive(self):
        return self._alive

    @property
    def x(self):
        if self.alive:
            return self._x
        return -1

    @property
    def y(self):
        if self.alive:
            return self._y
        return -1

    def valid(self, x, y):
        if not self.alive:
            return False
        return self.game.grid.valid(x, y)

    def steer(self, course):
        if course != self.last_course:
            self.last_course = course
            self.logger.debug("steer {}".format(course))
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


class Game(Base):
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

        def add_game(name):
            if name not in self.__games__:
                self.__games__[name] = Game(self, name)

        def game_info(payload):
            for game in payload:
                add_game(game['name'])

        self.adapter.on_game_info(game_info)

    @property
    def games(self):
        for _ in range(30):
            if self.__games__:
                return list(self.__games__.values())
            time.sleep(0.5)
        raise NotConnected()
