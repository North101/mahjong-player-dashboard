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


def tryParseInt(value):
  try:
    return int(value)
  except:
    return None


class Client:
  def __init__(self, poll: Poll, address: Tuple[str, int]):
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
  def state(self, state: 'ClientState'):
    self.client.state = state

  def on_server_data(self, server: socket.socket, event: int):
    if event & select.POLLHUP:
      self.on_server_disconnect(server)
    elif event & select.POLLIN:
      self.on_server_packet(server, self.read_packet())

  def on_server_disconnect(self, server: socket.socket):
    self.poll.unregister(server)
    server.close()

  def on_server_packet(self, server: socket.socket, packet: Packet):
    pass

  def on_input(self, input: str):
    pass

  def read_packet(self):
    return read_packet(self.client.socket)

  def send_packet(self, packet: Packet):
    send_packet(self.client.socket, packet)


class LobbyClientState(ClientState):
  def __init__(self, client: Client):
    self.client = client

  def on_server_packet(self, server: socket.socket, packet: Packet):
    if isinstance(packet, PlayerGameStateServerPacket):
      self.state = GameClientState(self.client, packet)


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
    if isinstance(packet, PlayerGameStateServerPacket):
      self.update_game(packet)
      self.print_info()

    elif isinstance(packet, DrawServerPacket):
      self.state = GameDrawClientState(self.client, self)

    elif isinstance(packet, RonServerPacket):
      self.state = GameRonClientState(self.client, self, packet.from_wind)

  def on_input(self, input: str):
    values = input.split()
    if not values:
      return

    elif values[0].lower() == 'riichi':
      self.on_input_riichi()

    elif values[0].lower() == 'tsumo':
      self.on_input_tsumo(values[1:])

    elif values[0].lower() == 'ron':
      self.on_input_ron(values[1:])

    elif values[0].lower() == 'draw':
      self.on_input_draw(values[1:])

  def on_input_riichi(self):
    self.send_packet(RiichiClientPacket())

  def on_input_tsumo(self, values: List[str]):
    if len(values) < 2:
      print('tsumo dealer_points points')
      return

    dealer_points = tryParseInt(values[0])
    if dealer_points is None:
      print('tsumo dealer_points points')
      return
    points = tryParseInt(values[1])
    if points is None:
      print('tsumo dealer_points points')
      return

    self.send_packet(TsumoClientPacket(dealer_points, points))

  def on_input_ron(self, values: List[str]):
    if len(values) < 2:
      print('ron wind points')
      return

    player_wind = self.player_wind(self.me)
    wind = {
        wind.name.lower(): wind
        for wind in Wind
        if wind != player_wind
    }.get(values[0].lower())
    if wind is None:
      print('ron wind points')
      return
    points = tryParseInt(values[1])
    if points is None:
      print('ron wind points')
      return

    self.send_packet(RonClientPacket(wind, points))

  def on_input_draw(self, values: List[str]):
    if len(values) >= 1:
      tenpai = TENPAI_VALUES.get(values[0].lower())
      if tenpai is None:
        print('draw [tenpai]')
    else:
      tenpai = None

    self.send_packet(DrawClientPacket(tenpai))

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
    if isinstance(packet, PlayerGameStateServerPacket):
      self.state = self.game_state
      self.state.on_server_packet(fd, packet)

  def on_input(self, input: str):
    value = input.split()
    if not value:
      return

    tenpai = TENPAI_VALUES.get(value[0].lower())
    if tenpai is not None:
      self.send_packet(DrawClientPacket(tenpai))
    else:
      self.print()


class GameRonClientState(ClientState):
  def __init__(self, client: Client, game_state: GameClientState, from_wind: Wind):
    self.client = client
    self.game_state = game_state
    self.from_wind = from_wind
    self.print()

  def print(self):
    sys.stdout.write('Ron?\n')
    sys.stdout.write('> ')
    sys.stdout.flush()

  def on_server_packet(self, fd: socket.socket, packet: Packet):
    if isinstance(packet, PlayerGameStateServerPacket):
      self.state = self.game_state
      self.state.on_server_packet(fd, packet)

  def on_input(self, input: str):
    value = input.split()
    points = tryParseInt(value[0]) or 0

    self.send_packet(RonClientPacket(self.from_wind, points))


def main():
  try:
    poll = Poll()
    client = Client(poll, ('127.0.0.1', 1246))
    client.start()
    while True:
      poll.poll()
  finally:
    poll.close()


if __name__ == '__main__':
  main()
