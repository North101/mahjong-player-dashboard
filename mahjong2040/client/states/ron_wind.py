import socket

from badger_ui.align import Center
from badger_ui.row import Row
from badger_ui.sized import SizedBox
from badger_ui.text import TextWidget
from mahjong2040.packets import (
    DrawServerPacket,
    GameStateServerPacket,
    Packet,
    RonWindClientPacket,
    RonWindServerPacket,
)
from mahjong2040.shared import Wind

import badger2040w
from badger_ui import App, Offset, Size

from .draw_menu import DrawMenuClientState
from .ron_score import RonScoreClientState
from .shared import GameReconnectClientState


class RonWindClientState(GameReconnectClientState):
  def __init__(self, client, players: list[int]):
    super().__init__(client)

    self.players = players

  def on_server_packet(self, server: socket.socket, packet: Packet):
    from .game import GameClientState

    super().on_server_packet(server, packet)
    if isinstance(packet, GameStateServerPacket):
      self.child = GameClientState(self.client, packet.game_state)

    elif isinstance(packet, RonWindServerPacket):
      self.child = RonScoreClientState(self.client, packet.from_wind)

    elif isinstance(packet, DrawServerPacket):
      self.child = DrawMenuClientState(self.client, packet.tenpai)

  def on_button(self, app: App, pressed: dict[int, bool]) -> bool:
    if pressed[badger2040w.BUTTON_A]:
      self.send_packet(RonWindClientPacket(self.players[-1]))
      return True

    elif pressed[badger2040w.BUTTON_B]:
      self.send_packet(RonWindClientPacket(self.players[-2]))
      return True

    elif pressed[badger2040w.BUTTON_C]:
      self.send_packet(RonWindClientPacket(self.players[-3]))
      return True

    return super().on_button(app, pressed)

  def render(self, app: App, size: Size, offset: Offset):
    super().render(app, size, offset)

    Row(children=[
        SizedBox(
            child=Center(child=TextWidget(
                text=Wind.name(wind),
                line_height=int(30 * 0.8),
                thickness=2,
                scale=0.8,
            )),
            size=Size(size.width // 3, size.height),
        )
        for wind in reversed(self.players)
    ]).render(app, size, offset)
