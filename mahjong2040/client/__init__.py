import select
import socket

from badger_ui import App
from mahjong2040.packets import PlayerStruct
from mahjong2040.poll import Poll
from mahjong2040.shared import Address, ClientGameState, GamePlayerTuple


class ServerDisconnectedError(Exception):
  pass


class Client(App):
  def __init__(self, poll: Poll, address: Address):
    from mahjong2040.client.states.base import ClientState

    super().__init__()

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


def start():
  from mahjong2040.client.states.game import GameClientState

  address = ('127.0.0.1', 1246)
  poll = Poll()
  try:
    client = Client(poll, address)
    client.child = GameClientState(client, ClientGameState(
        0,
        GamePlayerTuple(
            PlayerStruct(2500, False),
            PlayerStruct(2500, False),
            PlayerStruct(2500, False),
            PlayerStruct(2500, False),
        ),
    ))
    # client.start()
    while True:
      poll.poll()
      client.update()
  finally:
    poll.close()
