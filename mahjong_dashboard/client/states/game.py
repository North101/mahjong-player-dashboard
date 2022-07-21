import socket
from typing import TYPE_CHECKING

from mahjong_dashboard.packets import (GameDrawClientPacket, GameDrawServerPacket,
                             GameRiichiClientPacket, GameRonClientPacket,
                             GameRonServerPacket, GameStateServerPacket,
                             GameTsumoClientPacket, Packet)
from mahjong_dashboard.shared import (GamePlayerMixin, GameStateMixin, TenpaiState,
                            parseTenpai, tryParseInt, write, writelines)
from mahjong_dashboard.wind import Wind

from .game_draw import GameDrawClientState
from .game_ron import GameRonClientState
from .shared import GameReconnectClientState

if TYPE_CHECKING:
  from mahjong_dashboard.client import Client


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

  def on_input_tsumo(self, values: list[str]):
    if len(values) < 2:
      write('tsumo dealer_points points', input=True)
      return

    dealer_points = tryParseInt(values[0])
    if dealer_points is None:
      write('tsumo dealer_points points', input=True)
      return
    points = tryParseInt(values[1])
    if points is None:
      write('tsumo dealer_points points', input=True)
      return

    self.send_packet(GameTsumoClientPacket(dealer_points, points))

  def on_input_ron(self, values: list[str]):
    if len(values) < 2:
      write('ron wind points', input=True)
      return

    player_wind = self.player_wind(self.me)
    wind = {
        wind.name.lower(): wind
        for wind in Wind
        if wind != player_wind
    }.get(values[0].lower())
    if wind is None:
      write('ron wind points', input=True)
      return
    points = tryParseInt(values[1])
    if points is None:
      write('ron wind points', input=True)
      return

    self.send_packet(GameRonClientPacket(wind, points))

  def on_input_draw(self, values: list[str]):
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
    writelines((
        '----------------',
        f'Round: {self.round + 1}',
        f'Hand: {(self.game_state.hand % len(Wind)) + 1}',
        f'Repeat: {self.game_state.repeat}',
        f'Honba: {self.total_honba}',
        f'Riichi: {self.total_riichi}',
        '----------------',
    ))
    writelines((
        f'{wind.name}: {player}{" (Me)" if player == self.me else ""}'
        for (player, wind) in (
            (self.player_for_wind(wind), wind)
            for wind in Wind
        )
    ), input=True)
