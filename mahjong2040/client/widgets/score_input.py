import math

import badger2040
from badger_ui import App, Offset, Size, Widget


class ScoreInputWidget(Widget):
  def __init__(self):
    self.value = [
        0,
        0,
        0,
        0,
    ]
    self.index = 0

  @property
  def to_value(self):
    return sum(
        int(math.pow(10, len(self.value) + 2 - i)) * v
        for i, v in enumerate(self.value, start=1)
    )

  def on_button(self, app: App, pressed: dict[int, bool]) -> bool:
    if pressed[badger2040.BUTTON_A]:
      self.index = (self.index - 1) % len(self.value)
      return True

    elif pressed[badger2040.BUTTON_C]:
      self.index = (self.index + 1) % len(self.value)
      return True

    elif pressed[badger2040.BUTTON_UP]:
      self.value[self.index] = (self.value[self.index] + 1) % 10
      return True

    elif pressed[badger2040.BUTTON_DOWN]:
      self.value[self.index] = (self.value[self.index] - 1) % 10
      return True

    return super().on_button(app, pressed)

  def render(self, app: App, size: Size, offset: Offset):
    app.display.pen(0)
    app.display.thickness(2)

    value_scale = 2

    value_text = ''.join(str(v) for v in self.value) + '00'
    value_width = app.display.measure_text(value_text, scale=value_scale)
    app.display.text(
        value_text,
        offset.x + ((size.width - value_width) // 2),
        offset.y + (size.height // 2),
        scale=value_scale,
    )

    offset_x = app.display.measure_text(value_text[0:self.index], scale=value_scale)
    index_width = app.display.measure_text(value_text[self.index], scale=value_scale)
    start_x = offset.x + ((size.width - value_width) // 2) + offset_x
    start_y = offset.y + (size.height // 2) + (18 * value_scale)
    app.display.line(
        start_x,
        start_y,
        start_x + index_width,
        start_y,
    )
