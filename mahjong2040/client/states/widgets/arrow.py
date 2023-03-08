from badger_ui.base import App, Offset, Size, Widget

from mahjong2040.shared import IntEnum


class DirectionState(IntEnum):
  LEFT = 1
  UP = 2
  RIGHT = 4
  DOWN = 8


Direction = DirectionState()


class ArrowWidget(Widget):
  size = Size(60, 40)

  def __init__(self, arrow: int, lines: int):
    self.arrow = arrow
    self.lines = lines
  
  def measure(self, app: 'App', size: Size) -> Size:
    return self.size
  
  def draw_arrow(self, app: 'App', offset: Offset, x1: int, y1: int, x2: int, y2: int):
    app.display.triangle(
      offset.x,
      offset.y,
      offset.x + x1,
      offset.y + y1,
      offset.x + x2,
      offset.y + y2,
    )
  
  def draw_line(self, app: 'App', size: Size, offset: Offset, direction: int):
      half_width = size.width // 2
      half_height = size.height // 2
      x = offset.x + half_width
      y = offset.y + half_height
      thickness = 2
      thickness_offset = thickness // 2

      if direction == Direction.LEFT:
        width = -half_width
        height = thickness
        y -= thickness_offset
      elif direction == Direction.UP:
        width = thickness
        height = -half_height
        x -= thickness_offset
      elif direction == Direction.RIGHT:
        width = half_width
        height = thickness
        y -= thickness_offset
      elif direction == Direction.DOWN:
        width = thickness
        height = half_height
        x -= thickness_offset
      else:
        raise ValueError(direction)

      app.display.rectangle(
        x if width >= 0 else x + width,
        y if height >= 0 else y + height,
        width if width >= 0 else -width,
        height if height >= 0 else -height,
      )
  
  def render(self, app: 'App', size: 'Size', offset: 'Offset'):
    if self.arrow == Direction.LEFT:
      self.draw_arrow(
        app=app,
        offset=offset + Offset(0, (size.height // 2) - 1),
        x1=+8,
        y1=-6,
        x2=+8,
        y2=+6,
      )
    elif self.arrow == Direction.UP:
      self.draw_arrow(
        app=app,
        offset=offset + Offset((size.width // 2) - 1, 0),
        x1=-6,
        y1=+8,
        x2=+6,
        y2=+8,
      )
    elif self.arrow == Direction.RIGHT:
      self.draw_arrow(
        app=app,
        offset=offset + Offset(size.width, (size.height // 2) - 1),
        x1=-8,
        y1=-6,
        x2=-8,
        y2=+6,
      )
    elif self.arrow == Direction.DOWN:
      self.draw_arrow(
        app=app,
        offset=offset + Offset((size.width // 2) - 1, size.height),
        x1=-6,
        y1=-8,
        x2=+6,
        y2=-8,
      )

    for direction in Direction:
      if self.lines & direction:
        self.draw_line(
          app=app,
          size=size,
          offset=offset,
          direction=direction,
        )
