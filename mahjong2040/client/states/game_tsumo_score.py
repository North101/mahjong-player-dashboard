from badger_ui.align import Center
from badger_ui.base import App, Offset, Size
from badger_ui.text import TextWidget

import badger2040w
from mahjong2040.client.widgets.han_input import HanInputWidget
from mahjong2040.packets import TsumoClientPacket

from .shared import GameReconnectClientState


class GameTsumoScoreClientState(GameReconnectClientState):
  def __init__(self, client):
    super().__init__(client)

    self.score = HanInputWidget()

  def on_button(self, app: App, pressed: dict[int, bool]) -> bool:
    if pressed[badger2040w.BUTTON_B]:
      self.send_packet(TsumoClientPacket(self.score.tsumo(True), self.score.tsumo(False)))
      return True

    return self.score.on_button(app, pressed)

  def render(self, app: App, size: Size, offset: Offset):
    super().render(app, size, offset)

    Center(child=TextWidget(
        text='Tsumo',
        line_height=24,
        thickness=2,
        scale=0.8,
    )).render(app, Size(size.width, 24), offset)
    self.score.render(app, size, offset)
