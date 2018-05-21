import time
from typing import Iterable,List,Dict

from .adapter import TrazeMqttAdapter

class NotConnected(TimeoutError):
    pass

class Base:
    def __init__(self, parent:'Base', adapter:TrazeMqttAdapter=None, name:str=None):
        self.parent:Base = parent
        self.__adapter__:TrazeMqttAdapter = adapter
        self.name = name or self.__class__.__name__

    @property
    def adapter(self) -> TrazeMqttAdapter:
        if self.__adapter__:
            # print("Adapter: %s" % (type(self.__adapter__)))
            return self.__adapter__
        if self.parent:
            return self.parent.adapter
        return None

class Grid(Base):
    def __init__(self, parent:Base):
        super().__init__(parent)
        self.width = 0
        self.height = 0
        self.tiles = [[]]

        self.join()

    def join(self):
        def on_grid(payload:object):
            self.width = payload['width']
            self.height = payload['height']
            self.tiles = payload['tiles'][:] # clone

        self.adapter.on_grid(self.parent.name, on_grid)

#    def __onGrid__(self, payload:object):
#        self._x, self._y = [-1, -1]

#       myBike = None
#        self._trails = {}
#        for bike in payload['bikes']:
#            bike_id = bike['playerId']

#            self._trails[bike_id] = bike['trail']
#            if (bike_id == self._id):
#                myBike = bike

#        if myBike:
#            self._x, self._y = myBike['currentLocation']
#            if self._on_update and self._last != [self._x, self._y]:
#                # print(" call on_update() from ", self._last, "to", [self._x, self._y, ])
#                self._on_update()
#                self._last = [self._x, self._y]

class Player(Base):
    def __init__(self, parent:Base, name:str):
        super().__init__(parent, name=name)
        self._isAlive:bool = False
        self._x, self._y = [-1, -1]
        self._id:int = None
        self._secret:str = ''

#        self._trails:dict = {}
        self._last = []

    def join(self):
        if self.isAlive():
            print("Player '%s' is already alive!" % (self.name))
            return

        def on_join(payload:object):
            self._id = payload['id']
            self._secret = payload['secretUserToken']
            self._x, self._y = payload['position']
            
            print("Welcome '%s' (%s) at [%d, %d]!\n" % (self.name, self._id, self._x, self._y))

        def on_players(payload:object):
            isAlive = False
            for player in payload:
                if (player['id'] == self._id):
                    isAlive = True
                    break
            self._isAlive = isAlive

        self.adapter.on_player_info(self.parent.name, on_join)
        self.adapter.on_players(self.parent.name, on_players)

        # send join and wait for player
        self.adapter.publish_join(self.parent.name, self.name)
        for _ in range(30):
            if self.isAlive():
                return
            time.sleep(0.5)
        raise NotConnected()

    def isAlive(self) -> bool:
        return self._isAlive

    def steer(self, direction):
        self.adapter.publish_steer(self.parent.name, self._id, self._secret)

    def bail(self):
        self._isAlive:bool = False
        self.adapter.publish_bail(self.parent.name, self._id, self.name)

        self._x, self._y = [-1, -1]
        self._id:int = None
        self._secret:str = ''

    def die(self):
        self.bail()

    def __str__(self):
        return "%s(name=%s, id=%s, x=%d, y=%d)" % (self.__class__.__name__, self.name, self._id, self._x, self._y)

class Game(Base):
    def __init__(self, parent:Base, name:str):
        super().__init__(parent, name=name)
        self.player:Player = None
        self.grid:Grid = Grid(self)
        self._init:bool = True

    def join(self, player_name:str) -> Player:
        if self.player and self.player.name == player_name and self.player.isAlive():
            print("Player '%s' has already joined!" % (self.player.name))
            return None

        self.player:Player = Player(self, player_name)
        self.player.join()

        return self.player

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
