import select
import socket
import sys
from typing import TextIO, Tuple

from mahjong.packets import *
from mahjong.poll import Poll


class Client:
  socket: Type['socket.socket']
  state: Type['ClientState']

  def __init__(self, poll: Poll, address: Tuple[str, int]):
    self.poll = poll
    self.address = address
    self.state = ClientLobbyState(self)

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


class ClientState:
  def __init__(self, client: Client):
    self.client = client

  @property
  def poll(self):
    return self.client.poll

  def on_server_data(self, server: socket.socket, event: int):
    if event & select.POLLHUP:
      self.poll.unregister(server)
      self.on_server_disconnect(server)
    elif event & select.POLLIN:
      self.on_server_packet(server, read_packet(server))

  def on_server_disconnect(self, server: socket.socket):
    pass

  def on_server_packet(self, server: socket.socket, packet: Packet):
    raise NotImplementedError()

  def on_input(self, input: str):
    raise NotImplementedError()


class ClientLobbyState(ClientState):
  def __init__(self, client: Client):
    self.client = client

  def on_server_packet(self, server: socket.socket, packet: Packet):
    if type(packet) is PlayerGameStatePacket:
      self.client.state = ClientGameState(self.client, packet)

  def on_input(self, input: str):
    pass


class ClientGameState(ClientState):
  def __init__(self, client: Client, packet: PlayerGameStatePacket):
    self.client = client

    self.hand = packet.hand
    self.repeat = packet.repeat
    self.player_index = packet.player_index
    self.players = packet.players

    self.print_info()

  def on_server_packet(self, fd: socket.socket, packet: Packet):
    if type(packet) is PlayerGameStatePacket:
      self.hand = packet.hand
      self.repeat = packet.repeat
      self.player_index = packet.player_index
      self.players = packet.players

      self.print_info()

  def on_input(self, input: str):
    value = input.split()
    if not value:
      return
    elif value[0].lower() == 'riichi':
      send_msg(self.client.socket, RiichiPacket().pack())
    elif value[0].lower() == 'tsumo':
      dealer_points = int(value[1])
      points = int(value[2])
      send_msg(self.client.socket, TsumoPacket(dealer_points, points).pack())
    elif value[0].lower() == 'ron':
      wind = {
          wind.name.lower(): wind
          for wind in Wind
      }[value[1].lower()]
      points = int(value[2])
      send_msg(self.client.socket, RonPacket(wind, points).pack())
    elif value[0].lower() == 'draw':
      send_msg(self.client.socket, DrawPacket(wind, points).pack())

  @property
  def round(self):
    return self.hand % 4

  @property
  def me(self):
    return self.players[self.player_index]

  def player_for_wind(self, wind: Wind):
    return self.players[(self.hand + wind) % len(Wind)]

  def print_info(self):
    sys.stdout.writelines([
        '----------------\n',
        f'Round: {self.round}\n',
        f'Hand: {self.hand % 4}\n',
        f'Repeat: {self.repeat}\n',
        '----------------\n',
    ])

    for wind in Wind:
      player = self.player_for_wind(wind)
      sys.stdout.write(f'{wind.name}: {player}{" (Me)" if player == self.me else ""}\n',)
    sys.stdout.write('> ')
    sys.stdout.flush()


def main():
  poll = Poll()
  client = Client(poll, ('127.0.0.1', 1246))
  client.start()
  while True:
    poll.poll()


if __name__ == '__main__':
  main()
