import gc

import network
import uasyncio
from badger_ui.align import Bottom, Center
from badger_ui.base import App, Offset, Size, Widget, app_runner
from badger_ui.list import ListWidget
from badger_ui.text import TextWidget
from mahjong2040.shared import Address

import badger2040w
import WIFI_CONFIG
from network_manager import NetworkManager

from .poll import Poll


def isconnected():
  return network.WLAN(network.STA_IF).isconnected()

def ip_address():
  return network.WLAN(network.STA_IF).ifconfig()[0]


class MyApp(App):
  def __init__(self, port: int):
    super().__init__()

    self.port = port
    self.child = ConnectingScreen()
    self.connect()

  def status_handler(self, mode, status, ip):
    print(mode, status, ip)
    if status:
      self.child = SelectScreen(self.port)

    self.dirty = True
    self.update()

  def connect(self):
    if WIFI_CONFIG.COUNTRY == "":
        raise RuntimeError("You must populate WIFI_CONFIG.py for networking.")
    network_manager = NetworkManager(WIFI_CONFIG.COUNTRY, status_handler=self.status_handler)
    uasyncio.get_event_loop().run_until_complete(network_manager.client(WIFI_CONFIG.SSID, WIFI_CONFIG.PSK))
    gc.collect()


class ConnectingScreen(Widget):
  def render(self, app: App, size: Size, offset: Offset):
    app.display.set_pen(0)
    if isconnected():
      app.display.text("Connected!", 10, 10, 300, 0.5)
      app.display.text(ip_address(), 10, 30, 300, 0.5)
    else:
      app.display.text("Connecting...", 10, 10, 300, 0.5)


class SelectScreen(Widget):
  def __init__(self, port: int):
    super().__init__()

    self.port = port
    self.items = [
      MenuItem('Client', self.open_client),
      MenuItem('Server', self.open_server),
    ]
    self.child = ListWidget(
      item_height=21,
      item_count=len(self.items),
      item_builder=self.item_builder,
      page_item_count=2,
      selected_index=0,
    )
  
  def open_client(self):
    from .client import Client

    poll = Poll()
    client = Client(poll)
    client.broadcast(self.port)
    app_runner.app = client
  
  def open_server(self):
    from .client import Client, LocalClientServer
    from .server import Server

    poll = Poll()
    server = Server(poll)
    server.start(self.port)
    client = Client(poll)
    client.connect(LocalClientServer(server, client))
    app_runner.app = client

  def item_builder(self, index: int, selected: bool):
    return MenuItemWidget(
      item=self.items[index],
      selected=selected,
    )

  def on_button(self, app: App, pressed: dict[int, bool]) -> bool:
    return self.child.on_button(app, pressed)

  def render(self, app: App, size: Size, offset: Offset):
    Center(child=self.child).render(app, size, offset)

    Bottom(child=Center(child=TextWidget(
      text=f'IP: {ip_address()}',
      line_height=15,
      font='sans',
      thickness=2,
      scale=0.5,
    ))).render(app, size, offset)


class MenuItem:
  def __init__(self, name, callable):
    self.name = name
    self.callable = callable
  
  def __call__(self, *args, **kwargs):
    self.callable(*args, **kwargs)


class MenuItemWidget(Widget):
  def __init__(self, item: MenuItem, selected: bool):
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
      text=self.item.name,
      line_height=24,
      font='sans',
      thickness=2,
      color=15 if self.selected else 0,
      scale=0.8,
    )).render(app, size, offset)
