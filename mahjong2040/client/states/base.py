import badger2040w
from badger_ui import App, Offset, Size, Widget
from mahjong2040.packets import Packet
from mahjong2040.shared import Address

try:
  from mahjong2040.client import Client
except:
  pass


class ClientState(Widget):
  def __init__(self, client: 'Client'):
    print(self.__class__.__name__)
    self.client = client
    self.first_render = True
  
  def init(self):
    pass

  @property
  def child(self):
    return self.client.child

  @child.setter
  def child(self, child: 'ClientState'):
    self.client.child = child
  
  @property
  def settings(self):
    return self.client.settings
  
  def on_broadcast_packet(self, packet: Packet, address: Address):
    pass

  def on_server_packet(self, packet: Packet) -> bool:
    return False

  def send_packet(self, packet: Packet):
    self.client.send_packet(packet)

  def on_button(self, app: App, pressed: dict[int, bool]) -> bool:
    return False

  def render(self, app: App, size: Size, offset: Offset):
    if self.first_render:
      app.display.set_update_speed(badger2040w.UPDATE_FAST)
      self.first_render = False
    else:
      app.display.set_update_speed(badger2040w.UPDATE_TURBO)
