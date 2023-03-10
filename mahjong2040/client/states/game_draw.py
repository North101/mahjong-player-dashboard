from typing import Callable

import badger2040w
from badger_ui.align import Bottom, Center
from badger_ui.base import App, Offset, Size, Widget
from badger_ui.list import ListWidget
from badger_ui.stack import Stack
from badger_ui.text import TextWidget

from mahjong2040.client import Client
from mahjong2040.packets import DrawClientPacket, DrawTenpaiServerPacket, Packet
from mahjong2040.shared import Tenpai

from .shared import GameReconnectClientState


class GameDrawClientState(GameReconnectClientState):
  def __init__(self, client: 'Client', tenpai: int):
    super().__init__(client)

    self.tenpai = tenpai
    self.items = [
        MenuItem('Draw: Tenpai', self.select_tenpai),
        MenuItem('Draw: Noten', self.select_noten),
    ]
    self.list = ListWidget(
        item_height=24,
        item_count=len(self.items),
        item_builder=self.item_builder,
        page_item_count=len(self.items),
        selected_index=0,
    )

  def select_tenpai(self) -> bool:
    self.send_packet(DrawClientPacket(Tenpai.TENPAI))
    return True

  def select_noten(self) -> bool:
    self.send_packet(DrawClientPacket(Tenpai.NOTEN))
    return True

  def on_server_packet(self, packet: Packet) -> bool:
    if isinstance(packet, DrawTenpaiServerPacket):
      self.tenpai = packet.tenpai
      return True

    return super().on_server_packet(packet)

  def on_button(self, app: 'App', pressed: dict[int, bool]) -> bool:
    if self.tenpai == Tenpai.UNKNOWN:
      return self.list.on_button(app, pressed)

    return super().on_button(app, pressed)

  def item_builder(self, index: int, selected: bool):
    return MenuItemWidget(
        item=self.items[index],
        selected=selected,
    )

  def render(self, app: App, size: Size, offset: Offset):
    super().render(app, size, offset)

    if self.tenpai == Tenpai.UNKNOWN:
      Center(child=self.list).render(app, size, offset)
    else:
      Center(child=TextWidget(
          text='Tenpai' if self.tenpai == Tenpai.TENPAI else 'Noten',
          line_height=60,
          thickness=2,
          scale=2,
      )).render(app, size, offset)
      Bottom(child=Center(child=TextWidget(
          text=f'Waiting...',
          line_height=24,
          thickness=2,
          scale=0.8,
      ))).render(app, size, offset)


class MenuItem:
  def __init__(self, name: str, callable: Callable[[], bool]):
    self.name = name
    self.callable = callable

  def __call__(self) -> bool:
    return self.callable()


class MenuItemWidget(Widget):
  def __init__(self, item: MenuItem, selected: bool):
    self.item = item
    self.selected = selected

  def on_button(self, app: App, pressed: dict[int, bool]) -> bool:
    if pressed[badger2040w.BUTTON_B]:
      return self.item()

    return super().on_button(app, pressed)

  def render(self, app: 'App', size: Size, offset: Offset):
    Stack(children=[
        Background(color=0 if self.selected else 15),
        Center(child=TextWidget(
          text=self.item.name,
          line_height=24,
          thickness=2,
          scale=0.8,
          color=15 if self.selected else 0,
          )),
    ]).render(app, size, offset)


class Background(Widget):
  def __init__(self, color: int):
    super().__init__()

    self.color = color

  def render(self, app: 'App', size: Size, offset: Offset):
    app.display.set_pen(self.color)
    app.display.rectangle(
        offset.x,
        offset.y,
        size.width,
        size.height,
    )
