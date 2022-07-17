import socket
from typing import Type

from mahjong.wind import Wind

DRAW_POINTS = 1000
RIICHI_POINTS = 1000
TSUMO_HONBA_POINTS = 100
RON_HONBA_POINTS = 300

GamePlayers = tuple[
    Type['GamePlayerMixin'],
    Type['GamePlayerMixin'],
    Type['GamePlayerMixin'],
    Type['GamePlayerMixin'],
]


class ClientMixin:
  client: socket.socket


class GamePlayerMixin:
  points: int
  riichi: bool


class GameStateMixin:
  hand: int
  repeat: int
  bonus_honba: int
  bonus_riichi: int
  players: GamePlayers

  @property
  def round(self):
    return self.hand // len(Wind)

  @property
  def players_by_wind(self):
    for wind in Wind:
      yield wind, self.player_for_wind(wind)

  @property
  def total_honba(self):
    return self.repeat + self.bonus_honba

  @property
  def total_riichi(self):
    return self.bonus_riichi + sum(1 for player in self.players if player.riichi)

  def player_wind(self, player: GamePlayerMixin):
    return list(Wind)[(self.players.index(player) + self.hand) % len(Wind)]

  def player_index_for_wind(self, wind: Wind):
    return (self.hand + wind) % len(Wind)

  def player_for_wind(self, wind: Wind):
    return self.players[self.player_index_for_wind(wind)]
