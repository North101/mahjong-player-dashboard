from badger_ui.align import Center
from badger_ui.text import TextWidget
from mahjong2040.client.widgets.score_input import ScoreInputWidget
from mahjong2040.packets import TsumoClientPacket

import badger2040w
from badger_ui import App, Offset, Size

from .shared import GameReconnectClientState


class GameTsumoNonDealerClientState(GameReconnectClientState):
  def __init__(self, client, dealer_score: int):
    super().__init__(client)

    self.dealer_score = dealer_score
    self.score = ScoreInputWidget()

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
