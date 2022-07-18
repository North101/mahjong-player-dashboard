import socket

from mahjong.packets import *
from mahjong.poll import *
from mahjong.shared import *

from .base import *

if TYPE_CHECKING:
  from .game import GameServerState


class GameRonPlayer(ClientMixin):
  def __init__(self, client: socket.socket, points: Optional[int]):
    self.client = client
    self.points = points


class GameRonServerState(ServerState):
  def __init__(self, game_state: 'GameServerState', from_wind: Wind, players: List[GameRonPlayer], callback: Callable[[Wind, List[GameRonPlayer]], None]):
    self.game_state = game_state

    self.from_wind = from_wind
    self.players = players
    self.callback = callback

    for player in players:
      if player.points is not None:
        continue
      player.send_packet(GameRonServerPacket(from_wind))

  @property
  def server(self):
    return self.game_state.server

  def on_client_packet(self, client: socket.socket, packet: Packet):
    player = self.player_for_client(client)
    if not player:
      return
    elif isinstance(packet, GameRonClientPacket):
      self.on_player_ron(player, packet)

  def on_player_ron(self, player: GameRonPlayer, packet: GameRonClientPacket):
    player.points = packet.points

    if all((player.points is not None for player in self.players)):
      self.callback(self.from_wind, [
          player
          for player in self.players
          if player.points is not None and player.points > 0
      ])

  def player_for_client(self, client: socket.socket):
    try:
      return next((
          player
          for player in self.players
          if player.client == client
      ))
    except StopIteration:
      return None
