from mahjong2040.shared import TenpaiState
import socket

import badger2040
from badger_ui import App, Offset, Size
from badger_ui.center import Center
from badger_ui.row import Row
from badger_ui.sized import SizedBox
from badger_ui.text import TextWidget
from mahjong2040.packets import (DrawClientPacket, GameStateServerPacket,
                                 Packet)

from .shared import GameReconnectClientState


class DrawClientState(GameReconnectClientState):
  def __init__(self, client):
    self.client = client

  def on_server_packet(self, server: socket.socket, packet: Packet):
    from .game import GameClientState

    super().on_server_packet(server, packet)
    if isinstance(packet, GameStateServerPacket):
      self.child = GameClientState(self.client, packet.game_state)

  def on_button(self, app: 'App', pressed: dict[int, bool]) -> bool:
    if pressed[badger2040.BUTTON_A]:
      self.send_packet(DrawClientPacket(0))
      return True

    elif pressed[badger2040.BUTTON_B]:
      self.send_packet(DrawClientPacket(1))
      return True

    elif pressed[badger2040.BUTTON_C]:
      self.send_packet(DrawClientPacket(2))
      return True

    return super().on_button(app, pressed)

  def render(self, app: App, size: Size, offset: Offset):
    Row(children=[
        SizedBox(
            child=Center(child=TextWidget(
                text='Tenpai',
                line_height=int(30 * 0.8),
                thickness=2,
                scale=0.8,
            )),
            size=Size(size.width // 3, size.height),
        ),
        SizedBox(
            child=Center(child=TextWidget(
                text='Noten',
                line_height=int(30 * 0.8),
                thickness=2,
                scale=0.8,
            )),
            size=Size(size.width // 3, size.height),
        ),
        SizedBox(
            child=Center(child=TextWidget(
                text='Redraw',
                line_height=int(30 * 0.8),
                thickness=2,
                scale=0.8,
            )),
            size=Size(size.width // 3, size.height),
        ),
    ]).render(app, size, offset)
