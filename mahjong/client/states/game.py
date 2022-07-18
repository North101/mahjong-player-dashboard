import socket
from typing import TYPE_CHECKING, List

from mahjong.client.states.game_draw import GameDrawClientState
from mahjong.client.states.game_ron import GameRonClientState
from mahjong.client.states.shared import GameReconnectClientState
from mahjong.packets import (GameDrawClientPacket, GameDrawServerPacket,
                             GameRiichiClientPacket, GameRonClientPacket,
                             GameRonServerPacket, GameStateServerPacket,
                             GameTsumoClientPacket, Packet)
from mahjong.shared import (GamePlayerMixin, GameStateMixin, TenpaiState,
                            parseTenpai, tryParseInt)
from mahjong.wind import Wind

if TYPE_CHECKING:
  from mahjong.client import Client


class GameClientState(GameReconnectClientState, GameStateMixin[GamePlayerMixin]):
  def __init__(self, client: 'Client', packet: GameStateServerPacket):
    self.client = client

    self.update_game(packet)
    self.print()

  def on_server_packet(self, server: socket.socket, packet: Packet):
    super().on_server_packet(server, packet)

    if isinstance(packet, GameStateServerPacket):
      self.update_game(packet)
      self.print()

    elif isinstance(packet, GameDrawServerPacket):
      self.state = GameDrawClientState(self.client)

    elif isinstance(packet, GameRonServerPacket):
      self.state = GameRonClientState(self.client, packet.from_wind)

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
      print('\r', end='')
      print('tsumo dealer_points points')
      print('>', end=' ', flush=True)
      return

    dealer_points = tryParseInt(values[0])
    if dealer_points is None:
      print('\r', end='')
      print('tsumo dealer_points points')
      print('>', end=' ', flush=True)
      return
    points = tryParseInt(values[1])
    if points is None:
      print('\r', end='')
      print('tsumo dealer_points points')
      print('>', end=' ', flush=True)
      return

    self.send_packet(GameTsumoClientPacket(dealer_points, points))

  def on_input_ron(self, values: List[str]):
    if len(values) < 2:
      print('\r', end='')
      print('ron wind points')
      print('>', end=' ', flush=True)
      return

    player_wind = self.player_wind(self.me)
    wind = {
        wind.name.lower(): wind
        for wind in Wind
        if wind != player_wind
    }.get(values[0].lower())
    if wind is None:
      print('\r', end='')
      print('ron wind points')
      print('>', end=' ', flush=True)
      return
    points = tryParseInt(values[1])
    if points is None:
      print('\r', end='')
      print('ron wind points')
      print('>', end=' ', flush=True)
      return

    self.send_packet(GameRonClientPacket(wind, points))

  def on_input_draw(self, values: List[str]):
    if len(values) >= 1:
      tenpai = parseTenpai(values[0].lower())
    else:
      tenpai = TenpaiState.unknown

    self.send_packet(GameDrawClientPacket(tenpai))

  def update_game(self, packet: GameStateServerPacket):
    self.game_state = packet.game_state
    self.player_index = packet.player_index
    self.players = packet.players

  @property
  def me(self):
    return self.players[self.player_index]

  def print(self):
    print('\r', end='')
    print('----------------')
    print(f'Round: {self.round + 1}')
    print(f'Hand: {(self.game_state.hand % len(Wind)) + 1}')
    print(f'Repeat: {self.game_state.repeat}')
    print(f'Honba: {self.total_honba}')
    print(f'Riichi: {self.total_riichi}')
    print('----------------')

    for wind in Wind:
      player = self.player_for_wind(wind)
      print(f'{wind.name}: {player}{" (Me)" if player == self.me else ""}')
    print('>', end=' ', flush=True)
