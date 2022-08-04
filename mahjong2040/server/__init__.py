import select
import socket

from mahjong2040.poll import Poll
from mahjong2040.shared import Address


class Server:
  def __init__(self, poll: Poll, address: Address):
    from .states.base import ServerState
    from .states.lobby import LobbyServerState

    self.poll = poll
    self.address = address
    self.socket: socket.socket
    self.clients: list[socket.socket] = []
    self.child: ServerState = LobbyServerState(self)

  def start(self):
    host, port = self.address

    self.socket = socket.socket()
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.socket.bind(socket.getaddrinfo(host, port)[0][-1])

    print(f'Server is listing on the port {port}...')
    self.socket.listen()

    self.poll.register(self.socket, select.POLLIN, self.on_server_data)

  def on_server_data(self, fd: socket.socket, event: int):
    self.child.on_server_data(fd, event)

  def on_client_data(self, fd: socket.socket, event: int):
    self.child.on_client_data(fd, event)
