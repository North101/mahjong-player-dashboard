from badger_ui.align import Bottom, Center
from badger_ui.base import App, Offset, Size
from badger_ui.text import TextWidget

import badger2040
from mahjong2040.packets import TsumoClientPacket

from .shared import GameReconnectClientState
from .widgets.han_input import HanInputWidget


class GameTsumoScoreClientState(GameReconnectClientState):
  def __init__(self, client):
    super().__init__(client)

    self.score = HanInputWidget()

  def on_button(self, app: App, pressed: dict[int, bool]) -> bool:
    if pressed[badger2040.BUTTON_B]:
      self.send_packet(TsumoClientPacket(self.score.han_index, self.score.fu_index))
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
    Bottom(child=Center(child=TextWidget(
        text=f'{self.score.tsumo(False) * 100} / {self.score.tsumo(True) * 100}',
        line_height=30,
        thickness=2,
        scale=1,
    ))).render(app, size, offset)
