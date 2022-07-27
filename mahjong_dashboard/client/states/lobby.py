import socket

from mahjong_dashboard.packets import (LobbyPlayersServerPacket, Packet,
                             SetupSelectWindServerPacket)
from mahjong_dashboard.shared import write

from .base import ClientState
from .game_setup import GameSetupClientState


class LobbyClientState(ClientState):
  def on_server_packet(self, server: socket.socket, packet: Packet):
    if isinstance(packet, LobbyPlayersServerPacket):
      self.print(packet.count, packet.max_players)

    elif isinstance(packet, SetupSelectWindServerPacket):
      self.state = GameSetupClientState(self.client, packet.wind)

  def print(self, count: int, max_players: int):
    write(f'Players: {count} / {max_players}')
