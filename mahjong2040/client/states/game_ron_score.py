from badger_ui.align import Bottom, Center, Top
from badger_ui.base import App, Offset, Size
from badger_ui.text import TextWidget

import badger2040w
from mahjong2040.client.widgets.han_input import HanInputWidget
from mahjong2040.packets import (
    Packet,
    RonScoreClientPacket,
    RonScoreServerPacket,
    RonWindServerPacket,
)
from mahjong2040.shared import Wind

from .shared import GameReconnectClientState


class GameRonScoreClientState(GameReconnectClientState):
  def __init__(self, client, from_wind: int, dealer: bool):
    super().__init__(client)

    self.from_wind = from_wind
    self.dealer = dealer
    self.points = None
    self.score = HanInputWidget()

  def on_server_packet(self, packet: Packet) -> bool:
    if isinstance(packet, RonWindServerPacket):
      self.from_wind = packet.from_wind
      self.dealer = packet.dealer
      self.points = None
      return True

    elif isinstance(packet, RonScoreServerPacket):
      self.from_wind = packet.from_wind
      self.points = packet.points
      return True

    return super().on_server_packet(packet)

  def on_button(self, app: App, pressed: dict[int, bool]) -> bool:
    if pressed[badger2040w.BUTTON_B] and self.points is None:
      self.send_packet(RonScoreClientPacket(self.score.ron(self.dealer)))
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
