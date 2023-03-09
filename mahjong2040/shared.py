from typing import Generator, Generic, Tuple, TypeAlias, TypeVar

Address: TypeAlias = Tuple[str, int]


STARTING_POINTS = 250
DRAW_POINTS = 30
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
  
  def by_name(self, value: str):
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


_PlayerType = TypeVar('_PlayerType', bound=GamePlayerMixin)

class GameState(Generic[_PlayerType]):
  def __init__(
      self,
      players: tuple[_PlayerType, _PlayerType, _PlayerType, _PlayerType],
      starting_points: int,
      hand: int = 0,
      repeat: int = 0,
      bonus_honba: int = 0,
      bonus_riichi: int = 0,
  ):
    self.players = players
    self.starting_points = starting_points
    self.hand = hand
    self.repeat = repeat
    self.bonus_honba = bonus_honba
    self.bonus_riichi = bonus_riichi

  @property
  def round(self):
    return self.hand // len(Wind)

  @property
  def players_by_wind(self) -> Generator[tuple[int, _PlayerType], None, None]:
    for wind in range(len(Wind)):
      yield wind, self.player_for_wind(wind)

  @property
  def total_honba(self):
    return self.repeat + self.bonus_honba

  @property
  def total_riichi(self):
    return self.bonus_riichi + sum(1 for player in self.players if player.riichi)

  def player_wind(self, player: _PlayerType) -> int:
    return (self.players.index(player) - self.hand) % len(Wind)

  def player_index_for_wind(self, wind: int):
    return (wind + self.hand) % len(Wind)

  def player_for_wind(self, wind: int) -> _PlayerType:
    return self.players[self.player_index_for_wind(wind)]

  def __repr__(self):
    return f'{self.__class__.__name__}({self.hand}, {self.repeat}, {self.bonus_honba}, {self.bonus_riichi})'


class ClientGameState(GameState, Generic[_PlayerType]):
  def __init__(
      self,
      player_index: int,
      players: tuple[_PlayerType, _PlayerType, _PlayerType, _PlayerType],
      starting_points: int,
      hand: int = 0,
      repeat: int = 0,
      bonus_honba: int = 0,
      bonus_riichi: int = 0,
  ):
    super().__init__(players, starting_points, hand, repeat, bonus_honba, bonus_riichi)

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
