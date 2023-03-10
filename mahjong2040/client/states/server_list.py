import badger2040w
from badger_ui.align import Center
from badger_ui.base import Widget
from badger_ui.column import Column
from badger_ui.list import ListWidget
from badger_ui.sized import SizedBox
from badger_ui.text import TextWidget
from machine import Timer

from badger_ui import App, Offset, Size
from mahjong2040 import config
from mahjong2040.client import Client
from mahjong2040.packets import (
    BroadcastClientPacket,
    BroadcastServerPacket,
    Packet,
    send_packet_to,
)
from mahjong2040.shared import Address

from .base import ClientState


class ServerListClientState(ClientState):
  def __init__(self, client: Client, port: int):
    super().__init__(client)

    self.address = ('255.255.255.255', port)
    self.servers = []
    self.list = None

    self.timer = Timer(mode=Timer.PERIODIC, period=10000, callback=self.broadcast)
    self.broadcast()

  def broadcast(self, *args, **kwargs):
    if not self.client.socket:
      return

    send_packet_to(self.client.socket, BroadcastClientPacket(), self.address)

  def on_broadcast_packet(self, packet: Packet, address: Address):
    if isinstance(packet, BroadcastServerPacket):
      if address not in self.servers:
        if config.autoconnect:
          AddressItem(address, self.on_item_selected)()
          return

        self.servers.append(address)
        self.update_list()

  def update_list(self):
    if len(self.servers) > 0:
      self.list = ListWidget(
          item_height=24,
          item_count=len(self.servers),
          item_builder=self.item_builder,
          page_item_count=min(len(self.servers), 5),
          selected_index=0,
      )
    else:
      self.list = None

  def item_builder(self, index: int, selected: bool):
    return AddressItemWidget(
        item=AddressItem(self.servers[index], self.on_item_selected),
        selected=selected,
    )

  def on_item_selected(self, item: 'AddressItem'):
    from mahjong2040.client import RemoteClientServer
    self.timer.deinit()
    self.client.connect(RemoteClientServer(self.client, self.client.poll, item.address))

  def on_button(self, app: 'App', pressed: dict[int, bool]) -> bool:
    if self.list:
      return self.list.on_button(app, pressed)

    return super().on_button(app, pressed)

  def render(self, app: 'App', size: Size, offset: Offset):
    super().render(app, size, offset)

    Column(children=[
        TextWidget(
            text='Hosts',
            line_height=24,
            thickness=2,
            scale=0.8,
        ),
        self.list or Widget(),
    ]).render(app, size, offset)


class AddressItem:
  def __init__(self, address: Address, callable):
    self.address = address
    self.callable = callable

  def __call__(self):
    self.callable(self)


class AddressItemWidget(Widget):
  def __init__(self, item: AddressItem, selected: bool):
    self.item = item
    self.selected = selected

  def on_button(self, app: App, pressed: dict[int, bool]) -> bool:
    if pressed[badger2040w.BUTTON_B]:
      self.item()
      return True

    return super().on_button(app, pressed)

  def render(self, app: 'App', size: Size, offset: Offset):
    if self.selected:
      app.display.set_pen(0)
      app.display.rectangle(
          offset.x,
          offset.y,
          size.width,
          size.height,
      )

    Center(child=TextWidget(
        text=self.item.address[0],
        line_height=24,
        font='sans',
        thickness=2,
        color=15 if self.selected else 0,
        scale=0.8,
    )).render(app, size, offset)
