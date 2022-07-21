import socket

from mahjong_dashboard.packets import GameReconnectStatusServerPacket, Packet
from mahjong_dashboard.shared import writelines

from .base import ClientState


class GameReconnectClientState(ClientState):
  def on_server_packet(self, server: socket.socket, packet: Packet):
    if isinstance(packet, GameReconnectStatusServerPacket):
      writelines((
          f'Waiting for: ',
          ', '.join((wind.name for wind in packet.missing_winds)),
      ))
