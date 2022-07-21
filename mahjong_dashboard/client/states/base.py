import select
import socket
from typing import TYPE_CHECKING

import badger2040
from mahjong_dashboard.client import ServerDisconnectedError
from mahjong_dashboard.client.buttons import ButtonHandler
from mahjong_dashboard.packets import Packet, read_packet, send_packet

if TYPE_CHECKING:
  from mahjong_dashboard.client import Client


class ClientState:
  def __init__(self, client: 'Client'):
    self.client = client

  @property
  def poll(self):
    return self.client.poll

  @property
  def state(self):
    return self.client.state

  @state.setter
  def state(self, state: 'ClientState'):
    self.client.state = state

  def on_server_data(self, server: socket.socket, event: int):
    if event & select.POLLHUP:
      self.on_server_disconnect(server)
    elif event & select.POLLIN:
      self.on_server_packet(server, self.read_packet())

  def on_server_disconnect(self, server: socket.socket):
    address = server.getpeername()
    self.poll.unregister(server)
    server.close()

    raise ServerDisconnectedError(address)

  def on_server_packet(self, server: socket.socket, packet: Packet):
    pass

  def on_input(self, input: str):
    pass

  def on_button(self, handler: ButtonHandler, event: int):
    if event & select.POLLHUP:
      self.poll.unregister(handler)

    elif event & select.POLLIN:
      button = handler.read_button()
      if button.id == badger2040.BUTTON_A:
        print('BUTTON_A')
      elif button.id == badger2040.BUTTON_B:
        print('BUTTON_B')
      elif button.id == badger2040.BUTTON_C:
        print('BUTTON_C')
      elif button.id == badger2040.BUTTON_UP:
        print('BUTTON_UP')
      elif button.id == badger2040.BUTTON_DOWN:
        print('BUTTON_DOWN')
      elif button.id == badger2040.BUTTON_USER:
        print('BUTTON_USER')

  def read_packet(self):
    return read_packet(self.client.socket)

  def send_packet(self, packet: Packet):
    send_packet(self.client.socket, packet)

  def update_display(self):
    pass