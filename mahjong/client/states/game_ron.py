import socket
import sys
from typing import TYPE_CHECKING

from mahjong.packets import GameRonClientPacket, GameStateServerPacket, Packet
from mahjong.shared import tryParseInt
from mahjong.wind import Wind

from .base import ClientState

if TYPE_CHECKING:
  from mahjong.client import Client

  from .game import GameClientState


class GameRonClientState(ClientState):
  def __init__(self, client: 'Client', game_state: 'GameClientState', from_wind: Wind):
    self.client = client
    self.game_state = game_state
    self.from_wind = from_wind
    self.print()

  def print(self):
    sys.stdout.write('\n')
    sys.stdout.write('Ron? [points]\n')
    sys.stdout.write('> ')
    sys.stdout.flush()

  def on_server_packet(self, fd: socket.socket, packet: Packet):
    if isinstance(packet, GameStateServerPacket):
      self.state = self.game_state
      self.state.on_server_packet(fd, packet)

  def on_input(self, input: str):
    value = input.split()
    points = (len(value) >= 1 and tryParseInt(value[0])) or 0

    self.send_packet(GameRonClientPacket(self.from_wind, points))
