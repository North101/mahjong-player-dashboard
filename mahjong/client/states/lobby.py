import socket

from mahjong.packets import *
from mahjong.poll import *
from mahjong.shared import *

from .base import *
from .game_setup import *

if TYPE_CHECKING:
  from mahjong.client import Client


class LobbyClientState(ClientState):
  def __init__(self, client: 'Client'):
    self.client = client

  def on_server_packet(self, server: socket.socket, packet: Packet):
    if isinstance(packet, LobbyPlayersServerPacket):
      print(f'Players: {packet.count} / {packet.max_players}')

    elif isinstance(packet, SetupSelectWindServerPacket):
      self.state = GameSetupClientState(self.client, packet.wind)
