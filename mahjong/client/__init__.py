import select
import socket
import sys
from typing import TYPE_CHECKING, TextIO

from mahjong.poll import Poll
from mahjong.shared import Address

if TYPE_CHECKING:
  from mahjong.client.states.base import ClientState


class ServerDisconnectedError(Exception):
  def __init__(self, address: Address):
    self.address = address


class Client:
  def __init__(self, poll: Poll, address: Address):
    from mahjong.client.states.lobby import LobbyClientState

    self.poll = poll
    self.address = address
    self.socket: socket.socket
    self.state: ClientState = LobbyClientState(self)

  def start(self):
    (host, port) = self.address

    self.socket = socket.socket()
    print('Waiting for connection')
    self.socket.connect((host, port))

    self.poll.register(self.socket, select.POLLIN, self.on_server_data)
    self.poll.register(sys.stdin, select.POLLIN, self.on_input)

  def on_server_data(self, fd: socket.socket, event: int):
    self.state.on_server_data(fd, event)

  def on_input(self, fd: TextIO, event: int):
    self.state.on_input(fd.readline())
