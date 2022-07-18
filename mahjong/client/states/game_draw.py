import socket
import sys
from typing import TYPE_CHECKING

from mahjong.packets import GameDrawClientPacket, GameStateServerPacket, Packet
from mahjong.shared import parseTenpai

from .base import ClientState

if TYPE_CHECKING:
  from mahjong.client import Client

  from .game import GameClientState


class GameDrawClientState(ClientState):
  def __init__(self, client: 'Client', game_state: 'GameClientState'):
    self.client = client
    self.game_state = game_state
    self.print()

  def print(self):
    sys.stdout.write('\n')
    sys.stdout.write('Tenpai? [Yes/No]\n')
    sys.stdout.write('> ')
    sys.stdout.flush()

  def on_server_packet(self, fd: socket.socket, packet: Packet):
    if isinstance(packet, GameStateServerPacket):
      self.state = self.game_state
      self.state.on_server_packet(fd, packet)

  def on_input(self, input: str):
    value = input.split()
    if not value:
      return

    tenpai = parseTenpai(value[0].lower())
    if tenpai is not None:
      self.send_packet(GameDrawClientPacket(tenpai))
    else:
      self.print()
