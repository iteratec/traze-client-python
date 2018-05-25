import time
from typing import Iterable, List, Dict, Callable

from .adapter import TrazeMqttAdapter

class NotConnected(TimeoutError):
    pass

class Base:
    def __init__(self, parent, adapter:TrazeMqttAdapter=None, name:str=None):
        self._parent = parent
        self.__adapter__:TrazeMqttAdapter = adapter
        self._name = name or self.__class__.__name__

    @property
    def parent(self) -> 'Base':
        return self._parent

    @property
    def name(self) -> str:
        return self._name
        
    @property
    def adapter(self) -> TrazeMqttAdapter:
        if self.__adapter__:
            return self.__adapter__
        if self.parent:
            return self.parent.adapter
        return None

class Grid(Base):
    def __init__(self, game:'Game'):
        super().__init__(game)
        self.width = 0
        self.height = 0
        self.tiles = [[]]

    def join(self) -> 'Grid':
        def on_grid(payload:object):
            self.width = payload['width']
            self.height = payload['height']
            self.tiles = payload['tiles'][:] # clone

        self.adapter.on_grid(self.parent.name, on_grid)
        return self

    @property
    def game(self) -> 'Game':
        return self.parent

    def valid(self, x:int, y:int) -> bool:
        if (x < 0 or x >= self.width or y < 0 or y >= self.height):
            return False
        return self.tiles[x][y] == 0

class Player(Base):
    def __init__(self, game:'Game', name:str):
        super().__init__(game, name=name)
        self._alive:bool = False
        self._x, self._y = [-1, -1]
        self._id:int = None
        self._secret:str = ''
        self._last = [self._x, self._y]

    def join(self, on_update:Callable[[None], None]=None) -> 'Player':
        if self._alive:
            print("Player '%s' is already alive!" % (self.name))
            return
            
        def on_join(payload:object):
            self._id = payload['id']
            self._secret = payload['secretUserToken']
            self._x, self._y = payload['position']
            
            print("Welcome '%s' (%s) at [%d, %d]!\n" % (self.name, self._id, self._x, self._y))

        def on_players(payload:object):
            alive = False
            for player in payload:
                if (player['id'] == self._id):
                    alive = True
                    break
            self._alive = alive

            if alive and on_update:
                on_update()

        def on_grid(payload:object):
            if not self._alive:
                return

            myBike = None
            for bike in payload['bikes']:
                bike_id = bike['playerId']
                if (bike_id == self._id):
                    myBike = bike

            if myBike:
                self._x, self._y = myBike['currentLocation']
#                print("current location: ", self._x, self._y)

            if on_update and self._last != [self._x, self._y]:
                on_update()
                self._last = [self._x, self._y]

        self.adapter.on_grid(self.parent.name, on_grid)
        self.adapter.on_player_info(self.parent.name, on_join)
        self.adapter.on_players(self.parent.name, on_players)

        # send join and wait for player
        self.adapter.publish_join(self.parent.name, self.name)
        for _ in range(30):
            if self._alive:
                return self
            time.sleep(0.5)
        raise NotConnected()

    @property
    def game(self) -> 'Game':
        return self.parent

    @property
    def alive(self) -> bool:
        return self._alive

    @property
    def x(self) -> int:
        if self._alive:
            return self._x
        return -1

    @property
    def y(self) -> int:
        if self._alive:
            return self._y
        return -1

    def steer(self, course:str):
        self.adapter.publish_steer(self.parent.name, self._id, self._secret, course)

    def bail(self):
        self._alive:bool = False
        self.adapter.publish_bail(self.parent.name, self._id, self._secret)

        self._x, self._y = [-1, -1]
        self._id:int = None
        self._secret:str = ''

    def die(self):
        self.bail()

    def __str__(self):
        return "%s(name=%s, id=%s, x=%d, y=%d)" % (self.__class__.__name__, self.name, self._id, self._x, self._y)

class Game(Base):
    def __init__(self, world:'World', name:str):
        super().__init__(world, name=name)
        self._grid:Grid = Grid(self).join()

    @property
    def world(self) -> 'World':
        return self.parent

    @property
    def grid(self) -> 'Grid':
        return self._grid

class World(Base):
    def __init__(self):
        super().__init__(None, adapter=TrazeMqttAdapter()) 
        self.__games__:Dict[Game] = dict()

        def add_game(name:str):
            if name not in self.__games__:
                self.__games__[name] = Game(self, name)
                
        def game_info(payload:object):
            for game in payload:
                add_game(game['name'])

        self.adapter.on_game_info(game_info)

    @property
    def games(self) -> List[Game]:
        for _ in range(30):
            if self.__games__:
                return list(self.__games__.values())
            time.sleep(0.5)
        raise NotConnected()
