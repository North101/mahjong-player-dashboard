import socket

from mahjong2040.packets import GameReconnectStatusServerPacket, Packet

from .base import ClientState


class GameReconnectClientState(ClientState):
  def on_server_packet(self, packet: Packet):
    if isinstance(packet, GameReconnectStatusServerPacket):
      pass
