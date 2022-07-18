import socket
from typing import TYPE_CHECKING

from mahjong.packets import GameRonClientPacket, GameStateServerPacket, Packet
from mahjong.shared import (GamePlayerMixin, GamePlayerTuple, GameState,
                            tryParseInt)
from mahjong.wind import Wind

from .shared import GameReconnectClientState

if TYPE_CHECKING:
  from mahjong.client import Client


class GameRonClientState(GameReconnectClientState):
  def __init__(self, client: 'Client', from_wind: Wind):
    self.client = client
    self.from_wind = from_wind

    self.print()

  def on_server_packet(self, server: socket.socket, packet: Packet):
    from .game import GameClientState

    super().on_server_packet(server, packet)
    if isinstance(packet, GameStateServerPacket):
      self.state = GameClientState(self.client, packet)

  def on_input(self, input: str):
    value = input.split()
    points = (len(value) >= 1 and tryParseInt(value[0])) or 0

    self.send_packet(GameRonClientPacket(self.from_wind, points))

  def print(self):
    print('\r', end='')
    print('Ron? [points]')
    print('>', end=' ', flush=True)
