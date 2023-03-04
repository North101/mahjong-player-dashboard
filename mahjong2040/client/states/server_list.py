from badger_ui.align import Center
from badger_ui.base import Widget
from badger_ui.list import ListWidget
from badger_ui.text import TextWidget
from mahjong2040.packets import BroadcastClientPacket, Packet
from mahjong2040.shared import Address

import badger2040w
from badger_ui import App, Offset, Size

from .base import ClientState


class ServerListClientState(ClientState):
  def __init__(self, client):
    super().__init__(client)

    self.servers = []
    self.list = None
  
  def update_list(self):
    if len(self.servers) > 0:
      self.list = ListWidget(
        item_height=21,
        item_count=len(self.servers),
        item_builder=self.item_builder,
        page_item_count=min(len(self.servers), 6),
        selected_index=0,
      )
    else:
      self.list = None
  
  def on_broadcast_packet(self, packet: Packet, address: Address):
    if isinstance(packet, BroadcastClientPacket):
      self.servers.append(AddressItem(address, self.on_item_selected))
      self.update_list()

  def item_builder(self, index: int, selected: bool):
    return AddressItemWidget(
      item=self.servers[index],
      selected=selected,
    )

  def on_item_selected(self, item: 'AddressItem'):
    from mahjong2040.client import RemoteClientServer
    self.client.connect(RemoteClientServer(self.client.poll, item.address, self.client))

  def on_button(self, app: 'App', pressed: dict[int, bool]) -> bool:
    if self.list is not None:
      return self.list.on_button(app, pressed)

    return super().on_button(app, pressed)
  
  def render(self, app: 'App', size: Size, offset: Offset):
    if self.list is not None:
      Center(child=self.list).render(app, size, offset)
  

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
