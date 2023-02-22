import select
import socket

import network
from mahjong2040.poll import Poll
from mahjong2040.shared import Address

from badger_ui import App


class ServerDisconnectedError(Exception):
  pass


class Client(App):
  def __init__(self, poll: Poll, address: Address):
    from mahjong2040.client.states.base import ClientState

    super().__init__()

    self.poll = poll
    self.address = address
    self.socket: socket.socket = None
    self.child: ClientState

  def start(self):
    from mahjong2040.client.states.lobby import LobbyClientState

    host, port = self.address

    addrinfo = socket.getaddrinfo(host, port)[0][-1]

    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.poll.register(self.socket, select.POLLIN, self.on_server_data)

    print(f'Client connecting to {addrinfo}')
    self.socket.connect(addrinfo)

    self.child = LobbyClientState(self)
  
  def close(self):
    if self.socket is None:
      return
    
    self.socket.close()

  def on_server_data(self, fd: socket.socket, event: int):
    self.child.on_server_data(fd, event)
    self.dirty = True


def start():
  address = ('127.0.0.1', 1246)
  poll = Poll()
  try:
    client = Client(poll, address)
    client.start()
    while True:
      poll.poll()
      client.update()
  finally:
    poll.close()
