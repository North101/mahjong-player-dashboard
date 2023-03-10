from mahjong2040.packets import LobbyPlayersServerPacket
from mahjong2040.shared import Wind

from .base import ServerState
from .shared import ServerClient


class LobbyServerState(ServerState):
  def __init__(self, server):
    self.server = server

  def init(self):
    self.send_lobby_count()

  def on_client_join(self, client: ServerClient):
    super().on_client_join(client)

    self.send_lobby_count()
    if len(self.clients) == len(Wind):
      from .game_setup import GameSetupServerState
      self.child = GameSetupServerState(self.server)

  def on_client_leave(self, client: ServerClient):
    super().on_client_leave(client)
    self.send_lobby_count()

  def send_lobby_count(self):
    packet = LobbyPlayersServerPacket(len(self.clients), len(Wind))
    for client in self.clients:
      client.send_packet(packet)
