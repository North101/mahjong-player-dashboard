import socket
from typing import Generic, TypeVar

from mahjong2040.shared import RIICHI_POINTS, GameState

from .base import GamePlayer, ServerState

GamePlayerType = TypeVar('GamePlayerType', bound=GamePlayer)


class BaseGameServerStateMixin(Generic[GamePlayerType], ServerState):
  def __init__(self, server, game_state: GameState[GamePlayerType]):
    self.server = server
    self.game_state = game_state

  def on_client_disconnect(self, client: socket.socket):
    super().on_client_disconnect(client)

    player = self.player_for_client(client)
    if not player:
      return

    self.on_player_disconnect(player)

  def on_player_disconnect(self, player: GamePlayerType):
    from .game_reconnect import GameReconnectServerState

    self.child = GameReconnectServerState(self.server, self.game_state, self.on_players_reconnect)

  def on_players_reconnect(self, clients: list[socket.socket]):
    self.child = self
    for index, player in enumerate(self.game_state.players):
      player.client = clients[index]

  def player_for_client(self, client: socket.socket):
    try:
      return next((
          player
          for player in self.game_state.players
          if player.client == client
      ))
    except StopIteration:
      return None

  def take_riichi_points(self, winners: list[GamePlayerType]):
    winner = next((
        player
        for _, player in self.game_state.players_by_wind
        if player in winners
    ))

    winner.points += (RIICHI_POINTS * self.game_state.total_riichi)
    self.game_state.bonus_riichi = 0

  def reset_player_riichi(self):
    for player in self.game_state.players:
      player.riichi = False
  
  def redraw(self):
    self.game_state.bonus_honba += 1
    self.game_state.bonus_riichi = self.game_state.total_riichi

    self.reset_player_riichi()

  def repeat_hand(self, draw=False):
    if draw:
      self.game_state.bonus_riichi = self.game_state.total_riichi
    else:
      self.game_state.bonus_riichi = 0

    self.reset_player_riichi()
    self.game_state.repeat += 1

  def next_hand(self, draw=False):
    if draw:
      self.game_state.bonus_honba = self.game_state.total_honba + 1
      self.game_state.bonus_riichi = self.game_state.total_riichi
    else:
      self.game_state.bonus_honba = 0
      self.game_state.bonus_riichi = 0

    self.reset_player_riichi()
    self.game_state.hand += 1
    self.game_state.repeat = 0
