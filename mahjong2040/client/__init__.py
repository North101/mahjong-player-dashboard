import select
import socket

import badger2040
from badger_ui import App
from mahjong2040.poll import Poll
from mahjong2040.shared import Address


class ServerDisconnectedError(Exception):
  pass


class Client(App):
  def __init__(self, display: badger2040.Badger2040, poll: Poll, address: Address):
    from mahjong2040.client.states.base import ClientState

    super().__init__(display=display)

    self.poll = poll
    self.address = address
    self.socket: socket.socket
    self.child: ClientState

  def start(self):
    from mahjong2040.client.states.lobby import LobbyClientState

    (host, port) = self.address

    self.socket = socket.socket()
    print('Waiting for connection')
    self.socket.connect(socket.getaddrinfo(host, port)[0][-1])

    self.child = LobbyClientState(self)
    self.poll.register(self.socket, select.POLLIN, self.on_server_data)

  def on_server_data(self, fd: socket.socket, event: int):
    self.child.on_server_data(fd, event)
