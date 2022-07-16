import select
import socket
import sys
from typing import TextIO, Tuple

from mahjong.packets import *
from mahjong.poll import *
from mahjong.shared import *

TENPAI_VALUES = {
    'tenpai': True,
    'yes': True,
    'y': True,
    'true': True,

    'noten': False,
    'no': False,
    'n': False,
    'false': False,
}


class Client:
  socket: Type['socket.socket']
  state: Type['ClientState']

  def __init__(self, poll: Poll, address: Tuple[str, int]):
    self.poll = poll
    self.address = address
    self.state = LobbyClientState(self)

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

  @property
  def state(self):
    return self.client.state

  @state.setter
  def state(self, state: Type['ClientState']):
    self.client.state = state

  def on_server_data(self, server: socket.socket, event: int):
    if event & select.POLLHUP:
      self.poll.unregister(server)
      self.on_server_disconnect(server)
    elif event & select.POLLIN:
      self.on_server_packet(server, read_packet(server))

  def on_server_disconnect(self, server: socket.socket):
    raise ValueError()

  def on_server_packet(self, server: socket.socket, packet: Packet):
    raise NotImplementedError()

  def on_input(self, input: str):
    raise NotImplementedError()


class LobbyClientState(ClientState):
  def __init__(self, client: Client):
    self.client = client

  def on_server_packet(self, server: socket.socket, packet: Packet):
    if type(packet) is PlayerGameStateServerPacket:
      self.state = GameClientState(self.client, packet)

  def on_input(self, input: str):
    pass


class GameClientState(ClientState, GameStateMixin):
  def __init__(self, client: Client, packet: PlayerGameStateServerPacket):
    self.client = client

    self.update_game(packet)
    self.print_info()

  def update_game(self, packet: PlayerGameStateServerPacket):
    self.hand = packet.hand
    self.repeat = packet.repeat
    self.bonus_honba = packet.bonus_honba
    self.bonus_riichi = packet.bonus_riichi
    self.player_index = packet.player_index
    self.players = packet.players

  def on_server_packet(self, fd: socket.socket, packet: Packet):
    if type(packet) is PlayerGameStateServerPacket:
      self.update_game(packet)
      self.print_info()

    elif type(packet) is DrawServerPacket:
      self.state = GameDrawClientState(self.client, self)

  def on_input(self, input: str):
    value = input.split()
    if not value:
      return
    elif value[0].lower() == 'riichi':
      send_msg(self.client.socket, RiichiClientPacket().pack())
    elif value[0].lower() == 'tsumo':
      dealer_points = int(value[1])
      points = int(value[2])
      send_msg(self.client.socket, TsumoClientPacket(
          dealer_points, points).pack())
    elif value[0].lower() == 'ron':
      wind = {
          wind.name.lower(): wind
          for wind in Wind
      }[value[1].lower()]
      points = int(value[2])
      send_msg(self.client.socket, RonClientPacket(wind, points).pack())
    elif value[0].lower() == 'draw':
      tenpai = TENPAI_VALUES.get(value[0].lower())
      send_msg(self.client.socket, DrawClientPacket(tenpai).pack())

  @property
  def me(self):
    return self.players[self.player_index]

  def print_info(self):
    sys.stdout.writelines([
        '----------------\n',
        f'Round: {self.round + 1}\n',
        f'Hand: {(self.hand % len(Wind)) + 1}\n',
        f'Repeat: {self.repeat}\n',
        f'Honba: {self.total_honba}\n',
        f'Riichi: {self.total_riichi}\n',
        '----------------\n',
    ])

    for wind in Wind:
      player = self.player_for_wind(wind)
      sys.stdout.write(
          f'{wind.name}: {player}{" (Me)" if player == self.me else ""}\n',)
    sys.stdout.write('> ')
    sys.stdout.flush()


class GameDrawClientState(ClientState):
  def __init__(self, client: Client, game_state: GameClientState):
    self.client = client
    self.game_state = game_state
    self.print()

  def print(self):
    sys.stdout.write('Tenpai? [Yes/No]\n')
    sys.stdout.write('> ')
    sys.stdout.flush()

  def on_server_packet(self, fd: socket.socket, packet: Packet):
    if type(packet) is PlayerGameStateServerPacket:
      self.state = self.game_state
      self.state.on_server_packet(fd, packet)

  def on_input(self, input: str):
    value = input.split()
    if not value:
      return

    tenpai = TENPAI_VALUES.get(value[0].lower())
    if tenpai is not None:
      send_msg(self.client.socket, DrawClientPacket(tenpai).pack())
    else:
      self.print()


def main():
  try:
    poll = Poll()
    client = Client(poll, ('127.0.0.1', 1246))
    client.start()
    while True:
      poll.poll()
  finally:
    lookup = list(poll.lookup.values())
    for event_callback in lookup:
      fd = event_callback.fd
      poll.unregister(fd)


if __name__ == '__main__':
  main()
