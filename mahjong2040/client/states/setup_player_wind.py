import badger2040w
from badger_ui.align import Center, Top
from badger_ui.column import Column
from badger_ui.text import TextWidget

from badger_ui import App, Offset, Size
from mahjong2040 import config
from mahjong2040.client import Client
from mahjong2040.packets import (
    ConfirmWindServerPacket,
    GameStateServerPacket,
    Packet,
    SetupPlayerCountErrorServerPacket,
    SetupPlayerWindClientPacket,
    SetupPlayerWindServerPacket,
)
from mahjong2040.shared import Wind

from .base import ClientState


class SetupPlayerWindClientState(ClientState):
  def __init__(self, client: Client, wind: int):
    super().__init__(client)

    self.next_wind = wind
    self.confirmed_wind = None

  def init(self):
    if config.select_wind == self.next_wind and self.confirmed_wind is None:
      self.send_packet(SetupPlayerWindClientPacket(self.next_wind))

  def on_server_packet(self, packet: Packet) -> bool:
    if isinstance(packet, SetupPlayerWindServerPacket):
      self.next_wind = packet.wind
      self.init()

      return True

    elif isinstance(packet, ConfirmWindServerPacket):
      self.confirmed_wind = packet.wind
      return True

    elif isinstance(packet, SetupPlayerCountErrorServerPacket):
      from .lobby import LobbyClientState
      self.child = LobbyClientState(self.client)
      return True

    elif isinstance(packet, GameStateServerPacket):
      from .game import GameClientState
      self.child = GameClientState(self.client, packet.game_state)
      return True

    return super().on_server_packet(packet)

  def on_button(self, app: 'App', pressed: dict[int, bool]) -> bool:
    if pressed[badger2040w.BUTTON_B] and self.confirmed_wind is None:
      self.send_packet(SetupPlayerWindClientPacket(self.next_wind))
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

    if self.confirmed_wind is not None:
      Center(child=Column(children=[
          TextWidget(
              text=f'{Wind.name(self.confirmed_wind)}',
              line_height=30,
              thickness=2,
          ),
          TextWidget(
              text=(
                  f'Waiting for: {Wind.name((self.next_wind + 1) % len(Wind))}'
                  if (self.next_wind + 1) < len(Wind) else
                  f'Starting...'
              ),
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
