import socket
from typing import TYPE_CHECKING

from mahjong.packets import (GameStateServerPacket, Packet,
                             SetupConfirmWindServerPacket,
                             SetupNotEnoughServerPacket,
                             SetupSelectWindClientPacket,
                             SetupSelectWindServerPacket)
from mahjong.wind import Wind

from .base import ClientState

if TYPE_CHECKING:
  from mahjong.client import Client


class GameSetupClientState(ClientState):
  def __init__(self, client: 'Client', wind: Wind):
    self.client = client
    self.next_wind = wind

    self.print_select_wind()

  def on_server_packet(self, server: socket.socket, packet: Packet):
    from mahjong.client.states.game import GameClientState
    from mahjong.client.states.lobby import LobbyClientState

    if isinstance(packet, SetupSelectWindServerPacket):
      self.next_wind = packet.wind
      self.print_select_wind()

    elif isinstance(packet, SetupConfirmWindServerPacket):
      self.print_confirm_wind(packet.wind)

    elif isinstance(packet, SetupNotEnoughServerPacket):
      self.print_not_enough_players()
      self.state = LobbyClientState(self.client)

    elif isinstance(packet, GameStateServerPacket):
      self.state = GameClientState(self.client, packet)

  def on_input(self, input: str):
    self.send_packet(SetupSelectWindClientPacket(self.next_wind))

  def print_select_wind(self):
    print('\r', end='')
    print(f'{self.next_wind.name}? [Yes]')
    print('>', end=' ', flush=True)

  def print_confirm_wind(self, wind: Wind):
    print('\r', end='')
    print(f'You are: {wind.name}')

  def print_not_enough_players(self):
    print('\r', end='')
    print('Not enough players')
