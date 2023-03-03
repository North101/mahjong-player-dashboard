import socket
from typing import Callable

from badger_ui.align import Center
from badger_ui.base import App, Offset, Size, Widget
from badger_ui.list import ListWidget
from badger_ui.stack import Stack
from badger_ui.text import TextWidget
from mahjong2040.client import Client
from mahjong2040.packets import (
    DrawClientPacket,
    DrawServerPacket,
    GameStateServerPacket,
    Packet,
    RedrawClientPacket,
)
from mahjong2040.shared import GameState, Tenpai

import badger2040w

from .draw_menu import DrawMenuClientState
from .shared import GameReconnectClientState


class MenuClientState(GameReconnectClientState):
  def __init__(self, client: Client, game_state: GameState):
    super().__init__(client)

    self.game_state = game_state
    self.items = [
      MenuItem('Tsumo', self.select_tsumo),
      MenuItem('Ron', self.select_ron),
      MenuItem('Draw: Tenpai', self.select_tenpai),
      MenuItem('Draw: Noten', self.select_noten),
      MenuItem('Redraw', self.select_redraw),
    ]
    self.list = ListWidget(
      item_height=24,
      item_count=len(self.items),
      item_builder=self.item_builder,
      page_item_count=len(self.items),
      selected_index=0,
    )

  def select_tsumo(self) -> bool:
    from .tsumo_dealer import TsumoDealerClientState
    from .tsumo_nondealer import TsumoNonDealerClientState

    if self.game_state.player_wind(self.game_state.me) == 0:
      self.child = TsumoNonDealerClientState(self.client, 0)
    else:
      self.child = TsumoDealerClientState(self.client)
    return True

  def select_ron(self) -> bool:
    from .ron_wind import RonWindClientState

    self.child = RonWindClientState(self.client, [
        wind
        for wind, player in self.game_state.players_from_me
        if player != self.game_state.me
    ])
    return True

  def select_tenpai(self) -> bool:
    self.send_packet(DrawClientPacket(Tenpai.TENPAI))
    return True

  def select_noten(self) -> bool:
    self.send_packet(DrawClientPacket(Tenpai.NOTEN))
    return True

  def select_redraw(self) -> bool:
    self.send_packet(RedrawClientPacket())
    return True

  def on_server_packet(self, packet: Packet):
    from .game import GameClientState

    super().on_server_packet(packet)
    if isinstance(packet, GameStateServerPacket):
      self.child = GameClientState(self.client, packet.game_state)
    elif isinstance(packet, DrawServerPacket):
      self.child = DrawMenuClientState(self.client, packet.tenpai)

  def on_button(self, app: 'App', pressed: dict[int, bool]) -> bool:
    return self.list.on_button(app, pressed)

  def item_builder(self, index: int, selected: bool):
    return MenuItemWidget(
        item=self.items[index],
        selected=selected,
    )

  def render(self, app: App, size: Size, offset: Offset):
    super().render(app, size, offset)

    Center(child=self.list).render(app, size, offset)


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
