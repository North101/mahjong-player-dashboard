import socket
from typing import Tuple

from mahjong.packets import *
from mahjong.poll import *
from mahjong.shared import *

from .base import *
from .game_setup import *

if TYPE_CHECKING:
  from mahjong.server import Server


class LobbyServerState(ServerState):
  def __init__(self, server: 'Server'):
    self.server = server
    self.send_lobby_count()

  def on_client_connect(self, client: socket.socket, address: Tuple[str, int]):
    super().on_client_connect(client, address)

    self.send_lobby_count()

    if len(self.clients) == len(Wind):
      self.state = GameSetupServerState(self.server)

  def on_client_disconnect(self, client: socket.socket):
    super().on_client_disconnect(client)

    self.clients.remove(client)
    self.send_lobby_count()

  def send_lobby_count(self):
    packet = LobbyPlayersServerPacket(len(self.clients), len(Wind)).pack()
    for client in self.clients:
      send_msg(client, packet)
