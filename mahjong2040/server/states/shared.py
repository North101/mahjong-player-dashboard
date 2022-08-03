import socket

from mahjong2040.shared import (RIICHI_POINTS, GamePlayerMixin,
                                      GamePlayerTuple, GameState)

from .base import ClientMixin, ServerState


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


class BaseGameServerStateMixin(ServerState):
  def __init__(self, server, game_state: GameState, players: GamePlayerTuple):
    self.server = server
    self.game_state = game_state
    self.players = players

  def on_client_disconnect(self, client: socket.socket):
    super().on_client_disconnect(client)

    player = self.player_for_client(client)
    if not player:
      return

    self.on_player_disconnect(player)

  def on_player_disconnect(self, player: GamePlayer):
    from .game_reconnect import GameReconnectServerState

    self.child = GameReconnectServerState(self.server, self.game_state, self.players, self.on_players_reconnect)

  def on_players_reconnect(self, clients: list[socket.socket]):
    self.child = self
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

  def take_riichi_points(self, winners: list[GamePlayer]):
    winner = next((
        player
        for _, player in self.game_state.players_by_wind
        if player in winners
    ))

    winner.points += (RIICHI_POINTS * self.game_state.total_riichi)
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
