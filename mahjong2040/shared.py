from typing import Generic, Tuple, TypeAlias, TypeVar

Address: TypeAlias = Tuple[str, int]


STARTING_POINTS = 250
DRAW_POINTS = 10
RIICHI_POINTS = 10
TSUMO_HONBA_POINTS = 1
RON_HONBA_POINTS = 3


class IntEnum:
  def __init__(self):
    self.__items__ = [
        (key, value)
        for (key, value) in (
            (key, getattr(self, key))
            for key in dir(self)
        )
        if isinstance(value, int)
    ]
  
  def by_name(self, value):
    return next((
      item[1]
      for item in self.__items__
      if item[0] == value
    ))

  def name(self, value: int):
    return next((
      item[0]
      for item in self.__items__
      if item[1] == value
    ))

  def __iter__(self):
    for item in self.__items__:
      yield item[1]

  def __len__(self):
    return len(self.__items__)


class WindState(IntEnum):
  EAST = 0
  SOUTH = 1
  WEST = 2
  NORTH = 3


Wind = WindState()


class TenpaiState(IntEnum):
  UNKNOWN = 0
  TENPAI = 1
  NOTEN = 2


Tenpai = TenpaiState()


class GamePlayerMixin:
  points: int
  riichi: bool

  def __repr__(self) -> str:
    args = ', '.join([
      f'{key}={value}'
      for key, value in self.__dict__.items()
    ])
    return f'{self.__class__.__name__}({args})'


PlayerType = TypeVar('PlayerType', bound=GamePlayerMixin)


class GamePlayerTuple(Generic[PlayerType]):
  def __init__(
      self,
      player1: PlayerType,
      player2: PlayerType,
      player3: PlayerType,
      player4: PlayerType,
  ):
    self.player1 = player1
    self.player2 = player2
    self.player3 = player3
    self.player4 = player4

  def __iter__(self):
    yield self.player1
    yield self.player2
    yield self.player3
    yield self.player4

  def __getitem__(self, index: int):
    if index == 0:
      return self.player1
    elif index == 1:
      return self.player2
    elif index == 2:
      return self.player3
    elif index == 3:
      return self.player4
    raise IndexError(index)

  def index(self, item: PlayerType):
    if item == self.player1:
      return 0
    elif item == self.player2:
      return 1
    elif item == self.player3:
      return 2
    elif item == self.player4:
      return 3
    raise ValueError(item)

  def __repr__(self) -> str:
    args = ', '.join([
      f'{key}={value}'
      for key, value in self.__dict__.items()
    ])
    return f'{self.__class__.__name__}({args})'


class GameState(Generic[PlayerType]):
  def __init__(
      self,
      players: GamePlayerTuple[PlayerType],
      hand: int = 0,
      repeat: int = 0,
      bonus_honba: int = 0,
      bonus_riichi: int = 0,
  ):
    self.players = players
    self.hand = hand
    self.repeat = repeat
    self.bonus_honba = bonus_honba
    self.bonus_riichi = bonus_riichi

  @property
  def round(self):
    return self.hand // len(Wind)

  @property
  def players_by_wind(self):
    for wind in range(len(Wind)):
      yield wind, self.player_for_wind(wind)

  @property
  def total_honba(self):
    return self.repeat + self.bonus_honba

  @property
  def total_riichi(self):
    return self.bonus_riichi + sum(1 for player in self.players if player.riichi)

  def player_wind(self, player: PlayerType):
    return (self.players.index(player) - self.hand) % len(Wind)

  def player_index_for_wind(self, wind: int):
    return (wind + self.hand) % len(Wind)

  def player_for_wind(self, wind: int) -> GamePlayerMixin:
    return self.players[self.player_index_for_wind(wind) % len(Wind)]

  def __repr__(self):
    return f'{self.__class__.__name__}({self.hand}, {self.repeat}, {self.bonus_honba}, {self.bonus_riichi})'


class ClientGameState(GameState):
  def __init__(
      self,
      player_index: int,
      players: 'GamePlayerTuple',
      hand: int = 0,
      repeat: int = 0,
      bonus_honba: int = 0,
      bonus_riichi: int = 0,
  ):
    super().__init__(players, hand, repeat, bonus_honba, bonus_riichi)

    self.player_index = player_index

  @property
  def me(self):
    return self.players[self.player_index]

  @property
  def players_from_me(self):
    for wind in range(len(Wind)):
      wind = (wind + self.player_index - self.hand) % len(Wind)
      yield wind, self.player_for_wind(wind)

  def __repr__(self) -> str:
    args = ', '.join([
      f'{key}={value}'
      for key, value in self.__dict__.items()
    ])
    return f'{self.__class__.__name__}({args})'
