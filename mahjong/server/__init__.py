import select
import socket

from mahjong.poll import Poll
from mahjong.shared import Address

from .states.base import ServerState
from .states.lobby import LobbyServerState
from .states.shared import ClientList


class Server:
  def __init__(self, poll: Poll, address: Address):
    self.poll = poll
    self.address = address
    self.socket: socket.socket
    self.clients = ClientList()
    self.state: ServerState = LobbyServerState(self)

  def start(self):
    host, port = self.address

    self.socket = socket.socket()
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.socket.bind((host, port))

    print(f'Server is listing on the port {port}...')
    self.socket.listen()

    self.poll.register(self.socket, select.POLLIN, self.on_server_data)

  def on_server_data(self, fd: socket.socket, event: int):
    self.state.on_server_data(fd, event)

  def on_client_data(self, fd: socket.socket, event: int):
    self.state.on_client_data(fd, event)
