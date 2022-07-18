import socket

from mahjong.client.states.base import ClientState
from mahjong.packets import GameReconnectStatusServerPacket, Packet


class GameReconnectClientState(ClientState):
  def on_server_packet(self, server: socket.socket, packet: Packet):
    if isinstance(packet, GameReconnectStatusServerPacket):
      print('\r', end='')
      print(f'Waiting for: ')
      print(', '.join((wind.name for wind in packet.missing_winds)))
