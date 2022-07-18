import socket
from typing import Tuple

from mahjong.packets import *
from mahjong.poll import *
from mahjong.shared import *

from .base import *

if TYPE_CHECKING:
  from mahjong.server import Server

  from .game import GameServerState


class GameDrawPlayer(ClientMixin):
  def __init__(self, client: socket.socket, tenpai: Optional[bool]):
    self.client = client
    self.tenpai = tenpai


DrawPlayerTuple = Tuple[
    GameDrawPlayer,
    GameDrawPlayer,
    GameDrawPlayer,
    GameDrawPlayer,
]


class GameDrawServerState(ServerState):
  def __init__(self, server: 'Server', game_state: 'GameServerState', players: DrawPlayerTuple):
    self.server = server
    self.game_state = game_state

    self.players = players
    for player in players:
      if player.tenpai is not None:
        continue
      player.send_packet(GameDrawServerPacket())

  def on_client_packet(self, client: socket.socket, packet: Packet):
    player = self.player_for_client(client)
    if isinstance(packet, GameDrawClientPacket):
      self.on_player_draw(player, packet)

  def on_player_draw(self, player: GameDrawPlayer, packet: GameDrawClientPacket):
    player.tenpai = packet.tenpai

    if all((player.tenpai is not None for player in self.players)):
      self.state = self.game_state
      self.state.on_player_draw_complete(self.players)

  def player_for_client(self, client: socket.socket):
    return next((
        player
        for player in self.players
        if player.client == client
    ))
