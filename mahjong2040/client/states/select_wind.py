import socket

from badger_ui.align import Center, Top
from badger_ui.column import Column
from badger_ui.text import TextWidget
from mahjong2040.packets import (
    ConfirmWindServerPacket,
    GameStateServerPacket,
    NotEnoughPlayersServerPacket,
    Packet,
    SelectWindClientPacket,
    SelectWindServerPacket,
)
from mahjong2040.shared import Wind

import badger2040w
from badger_ui import App, Offset, Size

from .base import ClientState


class SelectWindClientState(ClientState):
  def __init__(self, client, wind: int):
    super().__init__(client)

    self.next_wind = wind
    self.confirmed_wind = -1

  def on_server_packet(self, server: socket.socket, packet: Packet):
    from .game import GameClientState
    from .lobby import LobbyClientState

    if isinstance(packet, SelectWindServerPacket):
      self.next_wind = packet.wind

    elif isinstance(packet, ConfirmWindServerPacket):
      self.confirmed_wind = packet.wind

    elif isinstance(packet, NotEnoughPlayersServerPacket):
      self.child = LobbyClientState(self.client)

    elif isinstance(packet, GameStateServerPacket):
      self.child = GameClientState(self.client, packet.game_state)

  def on_button(self, app: 'App', pressed: dict[int, bool]) -> bool:
    if pressed[badger2040w.BUTTON_B] and self.confirmed_wind < 0:
      self.send_packet(SelectWindClientPacket(self.next_wind))
      return True

    return super().on_button(app, pressed)

  def render(self, app: App, size: Size, offset: Offset):
    super().render(app, size, offset)

    Top(child=Center(child=TextWidget(
      text='Player Wind',
      line_height=24,
      thickness=2,
      scale=0.8,
    ))).render(app, size, offset)

    if self.confirmed_wind >= 0:
      Center(child=Column(children=[
          TextWidget(
              text=f'{Wind.name(self.confirmed_wind)}',
              line_height=30,
              thickness=2,
          ),
          TextWidget(
              text=f'Waiting for: {Wind.name((self.next_wind + 1) % len(Wind))}',
              line_height=21,
              thickness=2,
              scale=0.7,
          ),
      ])).render(app, size, offset)
    else:
      Center(child=TextWidget(
          text=f'{Wind.name(self.next_wind)}?',
          line_height=30,
          thickness=2,
      )).render(app, size, offset)
