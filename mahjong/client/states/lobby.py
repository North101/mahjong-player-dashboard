import socket
from typing import TYPE_CHECKING

from mahjong.packets import (LobbyPlayersServerPacket, Packet,
                             SetupSelectWindServerPacket)

from .base import ClientState
from .game_setup import GameSetupClientState

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
