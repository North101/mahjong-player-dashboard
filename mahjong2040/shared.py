from collections import namedtuple

from mahjong2040.wind import Wind

Address = namedtuple('Address', [
    'host',
    'port',
])


def writelines(lines: list[str], input=False):
  print('\r', end='')
  for line in lines:
    print(line)
  if input:
    print('>')


def write(line: str, input=False):
  writelines([line], input=input)


DRAW_POINTS = 1000
RIICHI_POINTS = 1000
TSUMO_HONBA_POINTS = 100
RON_HONBA_POINTS = 300


TenpaiState = [
    'tenpai',
    'noten',
    'redraw',
]


class GameState:
  def __init__(
      self,
      players: 'GamePlayerTuple',
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

  def player_wind(self, player: 'GamePlayerMixin'):
    return (self.players.index(player) - self.hand) % len(Wind)

  def player_index_for_wind(self, wind: int):
    return (wind + self.hand) % len(Wind)

  def player_for_wind(self, wind: int):
    return self.players[self.player_index_for_wind(wind)]

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
      wind = (wind + self.player_index) % len(Wind)
      yield wind, self.player_for_wind(wind)

  def __repr__(self):
    return f'{self.__class__.__name__}({self.player_index}, {self.players}, {self.hand}, {self.repeat}, {self.bonus_honba}, {self.bonus_riichi})'


class GamePlayerMixin:
  points: int
  riichi: bool


class GamePlayerTuple:
  def __init__(
      self,
      player1: GamePlayerMixin,
      player2: GamePlayerMixin,
      player3: GamePlayerMixin,
      player4: GamePlayerMixin,
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

  def index(self, item: GamePlayerMixin):
    if item == self.player1:
      return 0
    elif item == self.player2:
      return 1
    elif item == self.player3:
      return 2
    elif item == self.player4:
      return 3
    raise ValueError(item)
