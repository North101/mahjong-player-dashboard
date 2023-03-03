import socket

from badger_ui.align import Center
from badger_ui.text import TextWidget
from mahjong2040.client.widgets.score_input import ScoreInputWidget
from mahjong2040.packets import (
    DrawServerPacket,
    GameStateServerPacket,
    Packet,
    RonWindServerPacket,
    TsumoClientPacket,
)

import badger2040w
from badger_ui import App, Offset, Size

from .draw_menu import DrawMenuClientState
from .ron_score import RonScoreClientState
from .shared import GameReconnectClientState


class TsumoNonDealerClientState(GameReconnectClientState):
  def __init__(self, client, dealer_score: int):
    super().__init__(client)

    self.dealer_score = dealer_score
    self.score = ScoreInputWidget()

  def on_server_packet(self, packet: Packet):
    from .game import GameClientState

    super().on_server_packet(packet)
    if isinstance(packet, GameStateServerPacket):
      self.child = GameClientState(self.client, packet.game_state)

    elif isinstance(packet, RonWindServerPacket):
      self.child = RonScoreClientState(self.client, packet.from_wind)

    elif isinstance(packet, DrawServerPacket):
      self.child = DrawMenuClientState(self.client, packet.tenpai)

  def on_button(self, app: App, pressed: dict[int, bool]) -> bool:
    if pressed[badger2040w.BUTTON_B]:
      self.send_packet(TsumoClientPacket(self.dealer_score, self.score.to_value))
      return True

    return self.score.on_button(app, pressed)

  def render(self, app: App, size: Size, offset: Offset):
    super().render(app, size, offset)

    Center(child=TextWidget(
        text='Non-Dealer',
        line_height=24,
        thickness=2,
        scale=0.8,
    )).render(app, Size(size.width, 24), offset)
    self.score.render(app, size, offset)
