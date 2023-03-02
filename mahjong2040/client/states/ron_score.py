import socket

from badger_ui.align import Bottom, Center, Top
from badger_ui.text import TextWidget
from mahjong2040.client.widgets.score_input import ScoreInputWidget
from mahjong2040.packets import (
    DrawServerPacket,
    GameStateServerPacket,
    Packet,
    RonScoreClientPacket,
    RonScoreServerPacket,
    RonWindServerPacket,
)
from mahjong2040.shared import Wind

import badger2040w
from badger_ui import App, Offset, Size

from .draw_menu import DrawMenuClientState
from .shared import GameReconnectClientState


class RonScoreClientState(GameReconnectClientState):
  def __init__(self, client, from_wind: int):
    super().__init__(client)

    self.from_wind = from_wind
    self.points = None
    self.score = ScoreInputWidget()

  def on_server_packet(self, server: socket.socket, packet: Packet):
    from .game import GameClientState

    super().on_server_packet(server, packet)
    if isinstance(packet, RonWindServerPacket):
      self.from_wind = packet.from_wind
      self.points = None
    
    elif isinstance(packet, RonScoreServerPacket):
      self.from_wind = packet.from_wind
      self.points = packet.points

    elif isinstance(packet, GameStateServerPacket):
      self.child = GameClientState(self.client, packet.game_state)

    elif isinstance(packet, DrawServerPacket):
      self.child = DrawMenuClientState(self.client, packet.tenpai)

  def on_button(self, app: App, pressed: dict[int, bool]) -> bool:
    if pressed[badger2040w.BUTTON_B] and self.points is None:
      self.send_packet(RonScoreClientPacket(self.score.to_value))
      return True

    return self.score.on_button(app, pressed)

  def render(self, app: App, size: Size, offset: Offset):
    super().render(app, size, offset)

    Top(child=Center(child=TextWidget(
        text=f'Ron: {Wind.name(self.from_wind)}',
        line_height=24,
        thickness=2,
        scale=0.8,
    ))).render(app, size, offset)
    if self.points is not None:
      Center(child=TextWidget(
        text=f'{self.points * 100}',
          line_height=60,
          thickness=2,
          scale=2,
      )).render(app, size, offset)
      Bottom(child=Center(child=TextWidget(
          text=f'Waiting...',
          line_height=24,
          thickness=2,
          scale=0.8,
      ))).render(app, size, offset)
    else:
      self.score.render(app, size, offset)
