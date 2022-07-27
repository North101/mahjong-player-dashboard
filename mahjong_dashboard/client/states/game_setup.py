import socket

from mahjong_dashboard.packets import (GameStateServerPacket, Packet,
                                       SetupConfirmWindServerPacket,
                                       SetupNotEnoughServerPacket,
                                       SetupSelectWindClientPacket,
                                       SetupSelectWindServerPacket)
from mahjong_dashboard.shared import write
from mahjong_dashboard.wind import Wind

from .base import ClientState


class GameSetupClientState(ClientState):
  def __init__(self, client, wind: int):
    self.client = client
    self.next_wind = wind

    self.print_select_wind()

  def on_server_packet(self, server: socket.socket, packet: Packet):
    from .game import GameClientState
    from .lobby import LobbyClientState

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
    write(f'{Wind[self.next_wind]}? [Yes]', input=True)

  def print_confirm_wind(self, wind: int):
    write(f'You are: {Wind[wind]}')

  def print_not_enough_players(self):
    write('Not enough players')
