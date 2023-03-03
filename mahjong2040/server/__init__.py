import select
import socket

from mahjong2040.packets import Packet, send_msg
from mahjong2040.poll import Poll
from mahjong2040.shared import Address


class Server:
  def __init__(self, poll: Poll, address: Address):
    from .states.base import ServerState
    from .states.lobby import LobbyServerState

    self.poll = poll
    self.address = address
    self.socket: socket.socket = None
    self.clients: list[socket.socket] = []
    self.child: ServerState = LobbyServerState(self)

  def start(self):
    host, port = self.address

    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.poll.register(self.socket, select.POLLIN, self.on_server_data)

    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.socket.bind(('', port))

    print(f'Server is listing on port {port}...')
    self.socket.listen()
  
  def add_client(self, client):
    self.child.on_client_connect(client)
    client.register_packet(self.on_client_packet)
  
  def close(self):
    if self.socket is None:
      return
    
    self.socket.close()

  def on_server_data(self, fd: socket.socket, event: int):
    self.child.on_server_data(fd, event)

  def on_client_data(self, fd: socket.socket, event: int):
    self.child.on_client_data(fd, event)
  
  def on_client_packet(self, fd: socket.socket, packet: Packet):
    self.child.on_client_packet(fd, packet)

  def send_msg(self, client: socket.socket, msg: bytes):
    send_msg(client, msg)
