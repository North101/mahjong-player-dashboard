import socket
from typing import TYPE_CHECKING, List, Tuple

from mahjong.shared import (RIICHI_POINTS, GamePlayerMixin, GameState,
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


GamePlayerTuple = Tuple[
    GamePlayer,
    GamePlayer,
    GamePlayer,
    GamePlayer,
]

ClientTuple = List[socket.socket]


class ReconnectableGameStateMixin(ServerState, GameStateMixin):
  def __init__(self, server: 'Server', game_state: GameState, players: GamePlayerTuple):
    self.server = server
    self.game_state = game_state
    self.players: GamePlayerTuple = players

  def on_client_disconnect(self, client: socket.socket):
    from .game_reconnect import GameReconnectServerState

    super().on_client_disconnect(client)

    player = self.player_for_client(client)
    if not player:
      return

    self.state = GameReconnectServerState(self, self.on_game_reconnect)

  def on_game_reconnect(self, clients: ClientTuple):
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
