import select
import socket

from badger_ui import App
from mahjong2040.packets import Packet, read_packet, read_packet_from, send_packet
from mahjong2040.poll import Poll
from mahjong2040.shared import Address

try:
  from mahjong2040.server import Server
  from mahjong2040.server.shared import LocalServerClient
except:
  pass


class ServerDisconnectedError(Exception):
  pass

class ClientServer:
  def connect(self):
    pass

  def send_packet(self, packet: Packet):
    pass
  
  def close(self):
    pass


class RemoteClientServer(ClientServer):
  def __init__(self, client: 'Client', poll: Poll, address: Address):
    self.client: 'Client' = client
    self.poll = poll
    self.address = address
    self.socket: socket.socket = None
  
  def connect(self):
    host, port = self.address
    addrinfo = socket.getaddrinfo(host, port)[0][-1]

    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.poll.register(self.socket, select.POLLIN, self.on_server_data)

    print(f'Client connecting to {addrinfo}')
    self.socket.connect(addrinfo)

  def on_server_data(self, server: socket.socket, event: int):
    if event & (select.POLLHUP | select.POLLERR | 32):
      self.on_server_disconnect(server)
    elif event & select.POLLIN:
      packet = read_packet(self.socket)
      if packet is not None:
        print(self.__class__.__name__, repr(packet))
        self.client.on_server_packet(packet)
      else:
        self.on_server_disconnect(server)
    else:
      print(event)

  def on_server_disconnect(self, server: socket.socket):
    self.dirty = True
    self.poll.unregister(server)
    server.close()

    raise ServerDisconnectedError()

  def send_packet(self, packet: Packet):
    send_packet(self.socket, packet)

  def close(self):
    if self.socket is None:
      return
    
    self.socket.close()


class LocalClientServer(ClientServer):
  def __init__(self, client: 'Client', server: 'Server'):
    self.client = LocalServerClient(client)
    self.server = server
  
  def connect(self):
    self.server.add_client(self.client)

  def send_packet(self, packet: Packet):
    self.server.on_client_packet(self.client, packet)

  def close(self):
    self.server.remove_client(self.client)


class Client(App):
  def __init__(self, poll: Poll):
    from mahjong2040.client.states.base import ClientState

    super().__init__()

    self.poll = poll
    self._child: ClientState = None
    self.socket: socket.socket = None
    self.server: ClientServer = None
    self.events: list[Packet] = []
  
  @property
  def child(self):
    return self._child

  @child.setter
  def child(self, value):
    if self._child is value:
      return

    self._child = value
    self._child.init()
  
  def broadcast(self, port: int):
    from .states.server_list import ServerListClientState

    self.close()
  
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.socket.setsockopt(socket.SOL_SOCKET, 32, 1)
    self.poll.register(self.socket, select.POLLIN, self.on_broadcast_data)

    self.child = ServerListClientState(self, port)

  def on_broadcast_data(self, _socket: socket.socket, event: int):
    if event & select.POLLIN:
      packet, address = read_packet_from(_socket)
      if not packet:
        return

      self.dirty = True
      self.child.on_broadcast_packet(packet, address)

  def connect(self, server: ClientServer):
    from mahjong2040.client.states.lobby import LobbyClientState

    self.close()

    self.server = server
    self.child = LobbyClientState(self)

    self.server.connect()
  
  def close(self):
    if self.socket is not None:
      self.poll.unregister(self.socket)
      self.socket.close()
      self.socket = None

    if self.server is not None:
      self.server.close()
      self.server = None

  def on_server_packet(self, packet: Packet):
    self.events.append(packet)

  def send_packet(self, packet: Packet):
    self.server.send_packet(packet)
  
  def update(self):
    self.poll.poll()
    while self.events:
      self.child.on_server_packet(self.events.pop(0))
      self.dirty = True
    return super().update()
