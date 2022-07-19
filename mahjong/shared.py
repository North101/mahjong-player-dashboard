from enum import IntEnum
from typing import Generic, Iterable, Protocol, TypeVar

from mahjong.wind import Wind

Address = tuple[str, int]


def writelines(lines: Iterable[str], input=False):
  print('\r', end='')
  for line in lines:
    print(line)
  if input:
    print('>', end=' ', flush=True)


def write(line, input=False):
  writelines((line,), input=input)


DRAW_POINTS = 1000
RIICHI_POINTS = 1000
TSUMO_HONBA_POINTS = 100
RON_HONBA_POINTS = 300


class TenpaiState(IntEnum):
  tenpai = 0
  noten = 1
  unknown = 2


TENPAI_VALUES = {'tenpai', 'yes', 'y', 'true'}
NOTEN_VALUES = {'noten', 'no', 'n', 'false'}


def parseTenpai(value: str):
  value = value.lower()
  if value in TENPAI_VALUES:
    return TenpaiState.tenpai
  elif value in NOTEN_VALUES:
    return TenpaiState.noten
  return TenpaiState.unknown


def tryParseInt(value):
  try:
    return int(value)
  except BaseException:
    return None


class GameState:
  def __init__(self, hand: int = 0, repeat: int = 0, bonus_honba: int = 0, bonus_riichi: int = 0):
    self.hand = hand
    self.repeat = repeat
    self.bonus_honba = bonus_honba
    self.bonus_riichi = bonus_riichi

  def __repr__(self):
    return f'{self.__class__.__name__}({self.hand}, {self.repeat}, {self.bonus_honba}, {self.bonus_riichi})'


class GamePlayerMixin(Protocol):
  points: int
  riichi: bool


T = TypeVar('T', bound=GamePlayerMixin)


class GamePlayerTuple(Generic[T]):
  def __init__(self, player1: T, player2: T, player3: T, player4: T):
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

  def index(self, item: T):
    if item == self.player1:
      return 0
    elif item == self.player2:
      return 1
    elif item == self.player3:
      return 2
    elif item == self.player4:
      return 3
    raise ValueError(item)


class GameStateMixin(Generic[T]):
  game_state: GameState
  players: GamePlayerTuple[T]

  @property
  def round(self):
    return self.game_state.hand // len(Wind)

  @property
  def players_by_wind(self):
    for wind in Wind:
      yield wind, self.player_for_wind(wind)

  @property
  def total_honba(self):
    return self.game_state.repeat + self.game_state.bonus_honba

  @property
  def total_riichi(self):
    return self.game_state.bonus_riichi + sum(1 for player in self.players if player.riichi)

  def player_wind(self, player: T):
    return Wind((self.players.index(player) + self.game_state.hand) % len(Wind))

  def player_index_for_wind(self, wind: Wind):
    return (wind + self.game_state.hand) % len(Wind)

  def player_for_wind(self, wind: Wind):
    return self.players[self.player_index_for_wind(wind)]
