from badger_ui.align import Center
from badger_ui.base import App, Offset, Size, Widget
from badger_ui.row import Row
from badger_ui.text import TextWidget

import badger2040
from mahjong2040 import score_calculator


class HanInputWidget(Widget):
  def __init__(self):
    self.han_index = 0
    self.fu_index = 0
    self.selected = 0

  def measure(self, app: 'App', size: Size) -> Size:
    return Size(size.width, 30)

  def tsumo(self, dealer: bool):
    return score_calculator.tsumo(self.han_index, self.fu_index, dealer)

  def ron(self, dealer: bool):
    return score_calculator.ron(self.han_index, self.fu_index, dealer)

  def on_button(self, app: App, pressed: dict[int, bool]) -> bool:
    if pressed[badger2040.BUTTON_A]:
      self.selected = (self.selected - 1) % 2
      return True

    elif pressed[badger2040.BUTTON_C]:
      self.selected = (self.selected + 1) % 2
      return True

    elif pressed[badger2040.BUTTON_UP]:
      if self.selected == 0:
        self.han_index = (self.han_index + 1) % len(score_calculator.han_lookup)
      elif self.selected == 1:
        self.fu_index = (self.fu_index + 1) % len(score_calculator.fu_lookup)
      return True

    elif pressed[badger2040.BUTTON_DOWN]:
      if self.selected == 0:
        self.han_index = (self.han_index - 1) % len(score_calculator.han_lookup)
      elif self.selected == 1:
        self.fu_index = (self.fu_index - 1) % len(score_calculator.fu_lookup)
      return True

    return super().on_button(app, pressed)

  def han(self):
    return score_calculator.han_lookup[self.han_index]

  def fu(self):
    return score_calculator.fu_lookup[self.fu_index]

  def render(self, app: App, size: Size, offset: Offset):
    Center(child=Row(children=[
        TextWidget(
            text=f'{self.han_index}H ',
            line_height=30,
            thickness=2,
            underline=self.selected == 0,
        ),
        TextWidget(
            text=f' {self.fu()}F',
            line_height=30,
            thickness=2,
            underline=self.selected == 1,
        ),
    ])).render(app, size, offset)
