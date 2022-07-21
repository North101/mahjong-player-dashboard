import socket
from typing import TYPE_CHECKING, Generic, Iterable, TypeVar

from mahjong.shared import (RIICHI_POINTS, GamePlayerMixin, GamePlayerTuple, GameState,
                            GameStateMixin)

from .base import ClientMixin, ServerState

if TYPE_CHECKING:
  from mahjong.server import Server


class GamePlayer(ClientMixin, GamePlayerMixin):
  def __init__(self, client: socket.socket, points: int, riichi: bool = False):
    self.client = client
    self.points = points
    self.riichi = riichi

  def declare_riichi(self):
    if not self.riichi:
      self.riichi = True
      self.points -= RIICHI_POINTS

  def take_points(self, other: 'GamePlayer', points: int):
    self.points += points
    other.points -= points


ClientList = list[socket.socket]


T = TypeVar('T', bound=GamePlayer)


class BaseGameServerStateMixin(Generic[T], ServerState, GameStateMixin[T]):
  def __init__(self, server: 'Server', game_state: GameState, players: GamePlayerTuple[T]):
    self.server = server
    self.game_state = game_state
    self.players = players

  def on_client_disconnect(self, client: socket.socket):
    super().on_client_disconnect(client)

    player = self.player_for_client(client)
    if not player:
      return

    self.on_player_disconnect(player)

  def on_player_disconnect(self, player: T):
    from .game_reconnect import GameReconnectServerState

    self.state = GameReconnectServerState(self.server, self.game_state, self.players, self.on_players_reconnect)

  def on_players_reconnect(self, clients: ClientList):
    self.state = self
    for index, player in enumerate(self.players):
      player.client = clients[index]

  def player_for_client(self, client: socket.socket):
    try:
      return next((
          player
          for player in self.players
          if player.client == client
      ))
    except StopIteration:
      return None

  def take_riichi_points(self, winners: Iterable[T]):
    winner = next((
        player
        for _, player in self.players_by_wind
        if player in winners
    ))

    winner.points += (RIICHI_POINTS * self.total_riichi)
    self.game_state.bonus_riichi = 0

  def reset_player_riichi(self):
    for player in self.players:
      player.riichi = False

  def repeat_hand(self, draw=False):
    if draw:
      self.game_state.bonus_riichi = self.total_riichi
    else:
      self.game_state.bonus_riichi = 0

    self.reset_player_riichi()
    self.game_state.repeat += 1

  def next_hand(self, draw=False):
    if draw:
      self.game_state.bonus_honba = self.game_state.repeat + 1
      self.game_state.bonus_riichi = self.total_riichi
    else:
      self.game_state.bonus_honba = 0
      self.game_state.bonus_riichi = 0

    self.reset_player_riichi()
    self.game_state.hand += 1
    self.game_state.repeat = 0
