import select
import socket
import sys
from typing import TYPE_CHECKING, TextIO

from mahjong.client.buttons import ButtonHandler
from mahjong.poll import Poll
from mahjong.shared import Address

if TYPE_CHECKING:
  from mahjong.client.states.base import ClientState


class ServerDisconnectedError(Exception):
  def __init__(self, address: Address):
    self.address = address


class Client:
  def __init__(self, poll: Poll, address: Address):
    self.poll = poll
    self.address = address
    self.socket: socket.socket

  def start(self):
    from mahjong.client.states.lobby import LobbyClientState

    (host, port) = self.address

    self.socket = socket.socket()
    print('Waiting for connection')
    self.socket.connect((host, port))

    self.button_handler = ButtonHandler()

    self.state: ClientState = LobbyClientState(self)
    self.poll.register(self.socket, select.POLLIN, self.on_server_data)
    self.poll.register(sys.stdin, select.POLLIN, self.on_input)
    self.poll.register(self.button_handler, select.POLLIN, self.on_button)

  def on_server_data(self, fd: socket.socket, event: int):
    self.state.on_server_data(fd, event)

  def on_button(self, fd: ButtonHandler, event: int):
    self.state.on_button(fd, event)

  def on_input(self, fd: TextIO, event: int):
    self.state.on_input(fd.readline())

  def update_display(self):
    self.state.update_display()
