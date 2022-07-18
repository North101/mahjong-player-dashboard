import socket
from typing import TYPE_CHECKING, Callable, Tuple

from mahjong.packets import (GameDrawClientPacket, GameDrawServerPacket,
                             GameStateServerPacket, Packet)
from mahjong.shared import DRAW_POINTS, GamePlayerTuple, GameState, TenpaiState
from mahjong.wind import Wind

from .shared import ClientTuple, GamePlayer, BaseGameServerStateMixin

if TYPE_CHECKING:
  from mahjong.server import Server


class GameDrawPlayer(GamePlayer):
  def __init__(self, client: socket.socket, points: int, riichi: bool, tenpai: TenpaiState):
    self.client = client
    self.points = points
    self.riichi = riichi
    self.tenpai = tenpai


class GameDrawServerState(BaseGameServerStateMixin[GameDrawPlayer]):
  def __init__(self, server: 'Server', game_state: GameState, players: GamePlayerTuple[GameDrawPlayer]):
    self.server = server
    self.game_state = game_state
    self.players = players

    for player in players:
      if player.tenpai is not None:
        continue
      player.send_packet(GameDrawServerPacket())

  def on_players_reconnect(self, clients: ClientTuple):
    super().on_players_reconnect(clients)

    for index, player in enumerate(self.players):
      player.send_packet(GameStateServerPacket(self.game_state, index, self.players))
      if player.tenpai is not None:
        continue
      player.send_packet(GameDrawServerPacket())

  def on_client_packet(self, client: socket.socket, packet: Packet):
    player = self.player_for_client(client)
    if not player:
      return
    elif isinstance(packet, GameDrawClientPacket):
      self.on_player_draw(player, packet)

  def on_player_draw(self, player: GameDrawPlayer, packet: GameDrawClientPacket):
    player.tenpai = packet.tenpai

    self.on_player_draw_complete()

  def on_player_draw_complete(self):
    from mahjong.server.states.game import GameServerState

    if any((player.tenpai == TenpaiState.unknown for player in self.players)):
      return

    winners = [
        player
        for player in self.players
        if player.tenpai == True
    ]
    for player in winners:
      for other_player in self.players:
        if player == other_player:
          continue
        player.take_points(other_player, DRAW_POINTS)

    if self.player_for_wind(Wind.EAST) in winners:
      self.repeat_hand(draw=True)
    else:
      self.next_hand(draw=True)

    self.state = GameServerState(self.server, self.game_state, self.players)
