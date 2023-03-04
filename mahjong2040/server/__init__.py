import select
import socket

from mahjong2040.packets import (
    BroadcastClientPacket,
    Packet,
    create_msg,
    read_packet,
    read_packet_from,
)
from mahjong2040.poll import Poll

from .shared import RemoteServerClient, ServerClient


class Server:
  def __init__(self, poll: Poll):
    from .states.base import ServerState
    from .states.lobby import LobbyServerState

    self.poll = poll
    self.broadcast: socket.socket = None
    self.socket: socket.socket = None
    self.clients: list[ServerClient] = []
    self.child: ServerState = LobbyServerState(self)

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
      if isinstance(packet, BroadcastClientPacket):
        _socket.sendto(create_msg(BroadcastClientPacket().pack()), address)
  
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
    self.child.on_client_join(client)

  def remove_client(self, client: ServerClient):
    self.clients.remove(client)
    self.child.on_client_leave(client)

  def on_server_data(self, _socket: socket.socket, event: int):
    if event & select.POLLIN:
      client, _ = _socket.accept()
      self.on_client_connect(client)
      self.poll.register(client, select.POLLIN, self.on_client_data)

  def on_client_data(self, _socket: socket.socket, event: int):
    if event & (select.POLLHUP | select.POLLERR | 32):
      self.on_client_disconnect(_socket)
    elif event & select.POLLIN:
      packet = read_packet(_socket)
      if packet is None:
        return

      client = self.client_from_socket(_socket)
      if client is None:
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
    self.child.on_client_packet(client, packet)
