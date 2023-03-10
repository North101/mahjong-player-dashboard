import socket
import typing

from mahjong2040.packets import Packet, send_packet

if typing.TYPE_CHECKING:
  from mahjong2040.client import Client

class ServerClient:
  def send_packet(self, packet: Packet):
    pass


class RemoteServerClient(ServerClient):
  _socket: socket.socket

  def __init__(self, _socket: socket.socket):
    self._socket = _socket

  def send_packet(self, packet: Packet):
    send_packet(self._socket, packet)


class LocalServerClient(ServerClient):
  def __init__(self, client: Client):
    self.client = client
  
  def send_packet(self, packet: Packet):
    self.client.on_server_packet(packet)
