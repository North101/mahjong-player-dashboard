from typing import Tuple

from mahjong.wind import Wind

DRAW_POINTS = 1000
RIICHI_POINTS = 1000
TSUMO_HONBA_POINTS = 100
RON_HONBA_POINTS = 300

TENPAI_VALUES = {
    'tenpai': True,
    'yes': True,
    'y': True,
    'true': True,

    'noten': False,
    'no': False,
    'n': False,
    'false': False,
}


def tryParseInt(value):
  try:
    return int(value)
  except BaseException:
    return None


GamePlayers = Tuple[
    'GamePlayerMixin',
    'GamePlayerMixin',
    'GamePlayerMixin',
    'GamePlayerMixin',
]


class GameState:
  def __init__(self, hand: int = 0, repeat: int = 0, bonus_honba: int = 0, bonus_riichi: int = 0):
    self.hand = hand
    self.repeat = repeat
    self.bonus_honba = bonus_honba
    self.bonus_riichi = bonus_riichi

  def __repr__(self):
    return f'{self.__class__.__name__}({self.hand}, {self.repeat}, {self.bonus_honba}, {self.bonus_riichi})'


class GamePlayerMixin:
  points: int
  riichi: bool


class GameStateMixin:
  game_state: GameState
  players: GamePlayers

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

  def player_wind(self, player: GamePlayerMixin):
    return Wind((self.players.index(player) + self.game_state.hand) % len(Wind))

  def player_index_for_wind(self, wind: Wind):
    return (wind + self.game_state.hand) % len(Wind)

  def player_for_wind(self, wind: Wind):
    return self.players[self.player_index_for_wind(wind)]
