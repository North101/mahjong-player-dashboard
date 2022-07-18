import socket
import sys

from mahjong.packets import *
from mahjong.poll import *
from mahjong.shared import *

from .base import *

if TYPE_CHECKING:
  from mahjong.client import Client


class GameSetupClientState(ClientState):
  def __init__(self, client: 'Client', wind: Wind):
    self.client = client
    self.wind = wind

    print('')
    print('Assigning Winds:')
    self.print_wind()

  def on_server_packet(self, server: socket.socket, packet: Packet):
    from mahjong.client.states.game import GameClientState
    from mahjong.client.states.lobby import LobbyClientState

    if isinstance(packet, SetupSelectWindServerPacket):
      self.wind = packet.wind
      self.print_wind()

    elif isinstance(packet, SetupConfirmWindServerPacket):
      print(f'You are: {packet.wind.name}')

    elif isinstance(packet, SetupNotEnoughServerPacket):
      print('')
      print('Not enough players')
      self.state = LobbyClientState(self.client)

    elif isinstance(packet, GameStateServerPacket):
      self.state = GameClientState(self.client, packet)

  def print_wind(self):
    sys.stdout.write('\n')
    sys.stdout.write(f'{self.wind.name}? [Yes]\n')
    sys.stdout.write('> ')
    sys.stdout.flush()

  def on_input(self, input: str):
    self.send_packet(SetupSelectWindClientPacket(self.wind))
