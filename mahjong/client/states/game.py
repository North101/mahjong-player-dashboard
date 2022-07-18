import socket
import sys

from mahjong.packets import *
from mahjong.poll import *
from mahjong.shared import *

from .base import *
from .game_draw import *
from .game_ron import *

if TYPE_CHECKING:
  from mahjong.client import Client


class GameClientState(ClientState, GameStateMixin):
  def __init__(self, client: 'Client', packet: GameStateServerPacket):
    self.client = client

    self.update_game(packet)
    self.print_info()

  def update_game(self, packet: GameStateServerPacket):
    self.hand = packet.hand
    self.repeat = packet.repeat
    self.bonus_honba = packet.bonus_honba
    self.bonus_riichi = packet.bonus_riichi
    self.player_index = packet.player_index
    self.players = packet.players

  def on_server_packet(self, fd: socket.socket, packet: Packet):
    if isinstance(packet, GameStateServerPacket):
      self.update_game(packet)
      self.print_info()

    elif isinstance(packet, GameDrawServerPacket):
      self.state = GameDrawClientState(self.client, self)

    elif isinstance(packet, GameRonServerPacket):
      self.state = GameRonClientState(
          self.client, self, packet.from_wind)

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
    self.send_packet(GameRiichiClientPacket())

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

    self.send_packet(GameTsumoClientPacket(dealer_points, points))

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

    self.send_packet(GameRonClientPacket(wind, points))

  def on_input_draw(self, values: List[str]):
    if len(values) >= 1:
      tenpai = TENPAI_VALUES.get(values[0].lower())
      if tenpai is None:
        print('draw [tenpai]')
    else:
      tenpai = None

    self.send_packet(GameDrawClientPacket(tenpai))

  @property
  def me(self):
    return self.players[self.player_index]

  def print_info(self):
    sys.stdout.write('\n')
    sys.stdout.write('----------------\n')
    sys.stdout.write(f'Round: {self.round + 1}\n')
    sys.stdout.write(f'Hand: {(self.hand % len(Wind)) + 1}\n')
    sys.stdout.write(f'Repeat: {self.repeat}\n')
    sys.stdout.write(f'Honba: {self.total_honba}\n')
    sys.stdout.write(f'Riichi: {self.total_riichi}\n')
    sys.stdout.write('----------------\n')

    for wind in Wind:
      player = self.player_for_wind(wind)
      sys.stdout.write(
          f'{wind.name}: {player}{" (Me)" if player == self.me else ""}\n',)
    sys.stdout.write('> ')
    sys.stdout.flush()
