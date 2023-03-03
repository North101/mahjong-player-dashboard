from mahjong2040.client import Client
from mahjong2040.packets import Packet

import badger2040w
from badger_ui import App, Offset, Size, Widget


class ClientState(Widget):
  def __init__(self, client: Client):
    print(self.__class__.__name__)
    self.client = client
    self.first_render = True

  @property
  def poll(self):
    return self.client.poll

  @property
  def child(self):
    return self.client.child

  @child.setter
  def child(self, child: 'ClientState'):
    self.client.child = child

  def on_server_packet(self, packet: Packet):
    pass

  def send_packet(self, packet: Packet):
    self.client.send_packet(packet)

  def read_packet(self):
    return self.client.read_packet()

  def on_button(self, app: App, pressed: dict[int, bool]) -> bool:
    return False

  def render(self, app: App, size: Size, offset: Offset):
    if self.first_render:
      app.display.set_update_speed(badger2040w.UPDATE_FAST)
      self.first_render = False
    else:
      app.display.set_update_speed(badger2040w.UPDATE_TURBO)
