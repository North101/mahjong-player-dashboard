import socket
from typing import TYPE_CHECKING, Callable, Tuple

from mahjong.packets import GameRonClientPacket, GameRonServerPacket, GameStateServerPacket, Packet
from mahjong.shared import GameState
from mahjong.wind import Wind

from .shared import ClientTuple, GamePlayer, ReconnectableGameStateMixin

if TYPE_CHECKING:
  from mahjong.server import Server


class GameRonPlayer(GamePlayer):
  def __init__(self, client: socket.socket, points: int, riichi: bool, ron: int):
    self.client = client
    self.points = points
    self.riichi = riichi
    self.ron = ron


RonPlayerTuple = Tuple[
    GameRonPlayer,
    GameRonPlayer,
    GameRonPlayer,
    GameRonPlayer,
]


class GameRonServerState(ReconnectableGameStateMixin):
  def __init__(self, server: 'Server', game_state: GameState, players: RonPlayerTuple,
               from_wind: Wind, callback: Callable[[Wind, RonPlayerTuple], None]):
    self.server = server
    self.game_state = game_state
    self.players: RonPlayerTuple = players
    self.from_wind = from_wind
    self.callback = callback

    for player in players:
      if player.ron >= 0:
        continue
      player.send_packet(GameRonServerPacket(from_wind))
  
  def on_game_reconnect(self, clients: ClientTuple):
    super().on_game_reconnect(clients)

    for index, player in enumerate(self.players):
      player.send_packet(GameStateServerPacket(self.game_state, index, self.players))
      if player.ron >= 0:
        continue
      player.send_packet(GameRonServerPacket(self.from_wind))

  def on_client_packet(self, client: socket.socket, packet: Packet):
    player = self.player_for_client(client)
    if not player:
      return
    elif isinstance(packet, GameRonClientPacket):
      self.on_player_ron(player, packet)

  def on_player_ron(self, player: GameRonPlayer, packet: GameRonClientPacket):
    player.ron = packet.points

    if all((player.ron >= 0 for player in self.players)):
      self.callback(self.from_wind, self.players)
