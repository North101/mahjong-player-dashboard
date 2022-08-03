import socket

from mahjong2040.packets import GameReconnectStatusServerPacket, Packet
from mahjong2040.shared import writelines
from mahjong2040.wind import Wind

from .base import ClientState


class GameReconnectClientState(ClientState):
  def on_server_packet(self, server: socket.socket, packet: Packet):
    if isinstance(packet, GameReconnectStatusServerPacket):
      writelines([
          f'Waiting for: ', ', '.join((Wind[wind] for wind in packet.missing_winds)),
      ])
