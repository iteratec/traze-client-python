import time
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

    def join(self):
        def on_grid(payload):
            self.width = payload['width']
            self.height = payload['height']
            self.tiles = payload['tiles'][:]

        self.adapter.on_grid(self.game.name, on_grid)
        return self

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
        self._alive = False
        self._x, self._y = [-1, -1]
        self._id = None
        self._secret = ''
        self._last = [self._x, self._y]

        def on_join(payload):
            self._id = payload['id']
            self._secret = payload['secretUserToken']
            self._x, self._y = payload['position']

            self.logger.debug("Welcome '%s' (%s) at [%d, %d]!\n" % (self.name, self._id, self._x, self._y))
            on_update()

        def on_players(payload):
            alive = False
            for player in payload:
                if (player['id'] == self._id):
                    alive = True
                    break
            self._alive = alive

        def on_grid(payload):
            if not self._alive:
                return

            myBike = None
            for bike in payload['bikes']:
                bike_id = bike['playerId']
                if (bike_id == self._id):
                    myBike = bike

            if myBike:
                self._x, self._y = myBike['currentLocation']

            if self._last != [self._x, self._y]:
                on_update()
                self._last = [self._x, self._y]

        self.adapter.on_grid(self.game.name, on_grid)
        self.adapter.on_player_info(self.game.name, on_join)
        self.adapter.on_players(self.game.name, on_players)

    def join(self):  # noqa: C901 - is too complex (15)
        if self._alive:
            self.logger.info("Player '%s' is already alive!" % (self.name))
            return

        # send join and wait for player
        self.adapter.publish_join(self.game.name, self.name)
        for _ in range(30):
            if self._alive:
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
        if self._alive:
            return self._x
        return -1

    @property
    def y(self):
        if self._alive:
            return self._y
        return -1

    def steer(self, course):
        self.adapter.publish_steer(self.game.name, self._id, self._secret, course)

    def bail(self):
        self._alive = False
        self.adapter.publish_bail(self.game.name, self._id, self._secret)

        self._x, self._y = [-1, -1]
        self._id = None
        self._secret = ''

    def __str__(self):
        return "%s(name=%s, id=%s, x=%d, y=%d)" % (self.__class__.__name__, self.name, self._id, self._x, self._y)


class Game(Base):
    def __init__(self, world, name):
        super().__init__(world, name=name)
        self._grid = Grid(self).join()

    @property
    def world(self):
        return self._parent

    @property
    def grid(self):
        return self._grid


class World(Base):
    def __init__(self, adapter=TrazeMqttAdapter()):
        super().__init__()
        self.__adapter__ = adapter
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
