import select
import socket

import badger2040w
from badger_ui import App, Offset, Size, Widget
from mahjong2040.client import Client, ServerDisconnectedError
from mahjong2040.packets import Packet, read_packet, send_packet


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

  def on_server_data(self, server: socket.socket, event: int):
    if event & select.POLLHUP:
      self.on_server_disconnect(server)
    elif event & select.POLLIN:
      packet = self.read_packet()
      if packet is not None:
        print(self.__class__.__name__, repr(packet))
        self.on_server_packet(server, packet)

  def on_server_disconnect(self, server: socket.socket):
    self.poll.unregister(server)
    server.close()

    raise ServerDisconnectedError()

  def on_server_packet(self, server: socket.socket, packet: Packet):
    pass

  def read_packet(self):
    return read_packet(self.client.socket)

  def send_packet(self, packet: Packet):
    send_packet(self.client.socket, packet)

  def on_button(self, app: App, pressed: dict[int, bool]) -> bool:
    return False

  def render(self, app: App, size: Size, offset: Offset):
    if self.first_render:
      app.display.set_update_speed(badger2040w.UPDATE_FAST)
      self.first_render = False
    else:
      app.display.set_update_speed(badger2040w.UPDATE_TURBO)
