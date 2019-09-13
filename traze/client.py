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


class Bike(Base, metaclass=ABCMeta):
    def __init__(self, game, id):
        super().__init__(game)        
        self.id = id
        self.x = -1
        self.y = -1
        self.direction = None
        self.trail = []

    def update(self, payload):
        self.x = payload['currentLocation'][0]
        self.y = payload['currentLocation'][1]
        self.direction = payload['direction']
        self.trail = copy.deepcopy(payload['trail'])

    @property
    def game(self):
        return self._parent

            
class Grid(Base, metaclass=ABCMeta):
    def __init__(self, game):
        super().__init__(game)
        self.width = 0
        self.height = 0
        self.tiles = [[]]
        self._bikes = {}
        self._removed_bikes = set()

        def on_grid(payload):
            self.update(payload)

        def on_ticker(payload):
            self._removed_bikes.add(payload['casualty'])

        self.adapter.on_grid(self.game.name, on_grid)
        self.adapter.on_ticker(self.game.name, on_ticker)

    def update(self, payload):
        self.width = payload['width']
        self.height = payload['height']
        self.tiles = copy.deepcopy(payload['tiles'])

        for bike_payload in payload['bikes']:
            id = bike_payload['playerId']
            if id in self._removed_bikes:
                if self._bikes.pop(id, None):
                    self.logger.debug("Removed bike: {}".format(id))
                continue
            
            bike = self._bikes.get(id, Bike(self.game, id))
            bike.update(bike_payload)
            
            self._bikes[id] = bike

    @property
    def bikes(self):
        return self._bikes.values()

    def bike(self, id):
        return self._bikes.get(id, None)

    @property
    def game(self):
        return self._parent

    def __getitem__(self, coordinates):
        x, y = coordinates
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise IndexError
        return self.tiles[x][y]


class Spectator(Base, metaclass=ABCMeta):
    def __init__(self, game):
        super().__init__(game, name=None)

        def on_ticker(payload):
            self.logger.debug("ticker: type={},casualty={},fragger={}".format(
                    payload['type'],payload['casualty'],payload['fragger']))

        def on_players(payload):
            for player_payload in payload:
                id = player_payload['id']
                bike = self.game.bike(id) or Bike(self.game, -1)
                self.logger.debug("player: id={}, name={}, frags={}, owned={}, trail_size={}".format(
                        id,player_payload['name'],player_payload['frags'],player_payload['owned'],len(bike.trail)))

        self.adapter.on_ticker(self.game.name, on_ticker)
        self.adapter.on_players(self.game.name, on_players)

    def watch(self, timeout=3600):
        time.sleep(timeout)

        self.destroy()

    @property
    def game(self):
        return self._parent

    def destroy(self):
        self.adapter.disconnect()

    def __str__(self):
        return "{}()".format(self.__class__.__name__)  # noqa


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

            self.game._grid.update(payload)
            
            # will be set with first steer command
            if self.game.bike(self._id):
                bike = self.game.bike(self._id)
                self._x, self._y = (bike.x, bike.y)

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
                self._joined = False
                self.on_dead()

                self.__reset__()

        self.adapter.on_player_info(self.game.name, on_join)
        self.adapter.on_ticker(self.game.name, on_ticker)
        self.adapter.on_grid(self.game.name, on_grid)

    def __reset__(self):
        self._id = None
        self._secret = None
        self._joined = False
        self._last_course = None
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
        return self.game.bike(self._id) != None

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    def valid(self, x, y):
        try:
            return self.game.grid[x, y] == 0
        except IndexError:
            return False

    def steer(self, course):
        if self._last_course == course:
            return
        
        self.logger.debug("steer {}".format(course))

        self._last_course = course
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

    @property
    def bikes(self):
        return self._grid.bikes

    def bike(self, id):
        return self._grid.bike(id)


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
