UPDATE_NORMAL = 0
UPDATE_MEDIUM = 1
UPDATE_FAST = 2
UPDATE_TURBO = 3

BUTTON_A = 12
BUTTON_B = 13
BUTTON_C = 14
BUTTON_UP = 15
BUTTON_DOWN = 11
BUTTON_USER = 23

WIDTH = 296
HEIGHT = 128


class Badger2040:
  def pen(self, color: int):
    pass

  def thickness(self, thickness: int):
    pass

  def text(self, text: str, x: int, y: int, scale=1.0, rotation=0.0):
    pass

  def measure_text(self, text: str, scale=1.0):
    pass

  def clear(self):
    pass

  def update(self):
    pass

  def update_speed(self, speed: int):
    pass

  def line(self, x: int, y: int, width: int, height):
    pass

  def rectangle(self, x: int, y: int, width: int, height):
    pass

  def image(self, data: bytearray, w=WIDTH, height=HEIGHT, x=0, y=0):
    pass

  def font(self, font: str):
    pass

  def icon(self, data: bytearray, icon_index: int, sheet_size: int, icon_size: int, dx: int, dy: int):
    pass
