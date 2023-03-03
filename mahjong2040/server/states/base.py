import select
import socket
import typing

from mahjong2040.packets import Packet, read_packet, send_packet
from mahjong2040.shared import RIICHI_POINTS, Address, GamePlayerMixin

try:
  if typing.TYPE_CHECKING:
    from mahjong2040.server import Server
except:
  pass


class ClientMixin:
  client: socket.socket

  def send_packet(self, packet: Packet):
    send_packet(self.client, packet)


class GamePlayer(ClientMixin, GamePlayerMixin):
  def __init__(self, client: socket.socket, points: int, riichi: bool = False):
    self.client = client
    self.points = points
    self.riichi = riichi

  def declare_riichi(self):
    if not self.riichi:
      self.riichi = True
      self.points -= RIICHI_POINTS

  def take_points(self, other: 'GamePlayer', points: int):
    self.points += points
    other.points -= points


class ServerState:
  def __init__(self, server: 'Server'):
    print(self.__class__.__name__)
    self.server = server

  @property
  def clients(self):
    return self.server.clients

  @property
  def child(self):
    return self.server.child

  @child.setter
  def child(self, child: 'ServerState'):
    self.server.child = child

  @property
  def poll(self):
    return self.server.poll

  def on_server_data(self, server: socket.socket, event: int):
    if event & select.POLLIN:
      client, _ = server.accept()
      self.on_client_connect(client)
      self.poll.register(client, select.POLLIN, self.server.on_client_data)

  def on_client_data(self, client: socket.socket, event: int):
    if event & select.POLLHUP:
      self.on_client_disconnect(client)
    elif event & select.POLLIN:
      packet = read_packet(client)
      if packet is not None:
        print(self.__class__.__name__, repr(packet))
        self.on_client_packet(client, packet)

  def on_client_connect(self, client: socket.socket):
    self.clients.append(client)

  def on_client_disconnect(self, client: socket.socket):
    self.clients.remove(client)
    self.poll.unregister(client)
    client.close()

  def on_client_packet(self, client: socket.socket, packet: Packet):
    print(repr(packet))

  def send_msg(self, client: socket.socket, msg: bytes):
    self.server.send_msg(client, msg)