import select
import socket
import typing

from mahjong2040.packets import (
    BroadcastClientPacket,
    BroadcastServerPacket,
    Packet,
    read_packet,
    read_packet_from,
    send_packet_to,
)
from mahjong2040.poll import Poll

from .shared import RemoteServerClient, ServerClient

if typing.TYPE_CHECKING:
  from .states.base import ServerState


class Server:
  def __init__(self, poll: Poll):
    from .states.lobby import LobbyServerState

    self.poll = poll
    self.broadcast: socket.socket | None = None
    self.socket: socket.socket | None = None
    self.clients: list[ServerClient] = []
    self._child: ServerState | None = None
    self.child = LobbyServerState(self)

  @property
  def child(self):
    return self._child

  @child.setter
  def child(self, value: ServerState):
    if self._child is value:
      return

    self._child = value
    self._child.init()

  def start(self, port: int):
    self.broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.poll.register(self.broadcast, select.POLLIN, self.on_broadcast_data)
    self.broadcast.bind(('', port))

    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.poll.register(self.socket, select.POLLIN, self.on_server_data)
    self.socket.bind(('', port))

    print(f'Server is listing on port {port}...')
    self.socket.listen()

  def close(self):
    if self.broadcast is not None:
      self.broadcast.close()

    if self.socket is not None:
      self.socket.close()

  def on_broadcast_data(self, _socket: socket.socket, event: int):
    if event & select.POLLIN:
      packet, address = read_packet_from(_socket)
      if isinstance(packet, BroadcastClientPacket) and address:
        send_packet_to(_socket, BroadcastServerPacket(), address)

  def client_from_socket(self, _socket: socket.socket):
    try:
      return next((
          client
          for client in self.clients
          if isinstance(client, RemoteServerClient) and client._socket == _socket
      ))
    except StopIteration:
      return None

  def add_client(self, client: ServerClient):
    self.clients.append(client)
    if self.child:
      self.child.on_client_join(client)

  def remove_client(self, client: ServerClient):
    self.clients.remove(client)
    if self.child:
      self.child.on_client_leave(client)

  def on_server_data(self, _socket: socket.socket, event: int):
    if event & select.POLLIN:
      client, _ = _socket.accept()
      self.on_client_connect(client)
      self.poll.register(client, select.POLLIN | select.POLLERR | select.POLLHUP | 32, self.on_client_data)

  def on_client_data(self, _socket: socket.socket, event: int):
    if event & (select.POLLHUP | select.POLLERR | 32):
      self.on_client_disconnect(_socket)
    elif event & select.POLLIN:
      packet = read_packet(_socket)
      client = self.client_from_socket(_socket)
      if client is None:
        return

      if packet is None:
        self.remove_client(client)
        return

      print(self.__class__.__name__, repr(packet))
      self.on_client_packet(client, packet)
    else:
      print(event)

  def on_client_connect(self, _socket: socket.socket):
    self.add_client(RemoteServerClient(_socket))

  def on_client_disconnect(self, _socket: socket.socket):
    client = self.client_from_socket(_socket)
    if client is not None:
      self.remove_client(client)

    self.poll.unregister(_socket)
    _socket.close()

  def on_client_packet(self, client: ServerClient, packet: Packet):
    if self.child:
      self.child.on_client_packet(client, packet)
