import select
import socket
import sys

from mahjong_dashboard.poll import Poll
from mahjong_dashboard.shared import Address


class ServerDisconnectedError(Exception):
  pass


class Client:
  def __init__(self, poll: Poll, address: Address):
    self.poll = poll
    self.address = address
    self.socket: socket.socket

  def start(self):
    from mahjong_dashboard.client.states.lobby import LobbyClientState

    (host, port) = self.address

    self.socket = socket.socket()
    print('Waiting for connection')
    self.socket.connect(socket.getaddrinfo(host, port)[0][-1])

    self.state = LobbyClientState(self)
    self.poll.register(self.socket, select.POLLIN, self.on_server_data)
    self.poll.register(sys.stdin, select.POLLIN, self.on_input)

  def on_server_data(self, fd: socket.socket, event: int):
    self.state.on_server_data(fd, event)

  def on_input(self, fd, event: int):
    self.state.on_input(fd.readline())

  def update_display(self):
    self.state.update_display()
