from badger_ui.base import App, Offset, Size, Widget
from badger_ui.padding import EdgeOffsets, Padding
from badger_ui.row import Row
from badger_ui.text import TextWidget

from mahjong2040.shared import Wind


class PlayerWidget(Widget):
  height = 40
  font = 'sans'
  thickness = 2
  absolute_points_scale = 1
  relative_points_scale = 0.8
  wind_scale = 0.6

  def __init__(self, points: int, wind: int, absolute: bool):
    self.points = points
    self.wind = wind
    self.absolute = absolute
  
  def points_scale(self):
    return self.absolute_points_scale if self.absolute else self.relative_points_scale
  
  def points_text(self):
    if self.absolute:
      return f'{self.points * 100}'
    return f'{"+" if self.points >= 0 else ""}{self.points * 100}'
  
  def wind_text(self):
    return Wind.name(self.wind)[0].upper()

  def width(self, app: App):
    app.display.set_font(self.font)
    app.display.set_thickness(self.thickness)
    points_width = app.display.measure_text(self.points_text(), scale=self.points_scale())
    wind_width = app.display.measure_text(self.wind_text(), scale=self.wind_scale)
    return points_width + wind_width
  
  def measure(self, app: 'App', size: Size) -> Size:
    return Size(self.width(app), self.height)
  
  def render(self, app: 'App', size: Size, offset: Offset):
    Padding(
      padding=EdgeOffsets(bottom=1),
      child=Row(children=[
        TextWidget(
            text=self.points_text(),
            line_height=size.height,
            font=self.font,
            thickness=self.thickness,
            scale=self.points_scale(),
        ),
        TextWidget(
            text=self.wind_text(),
            line_height=size.height,
            font=self.font,
            thickness=self.thickness,
            scale=self.wind_scale,
        ),
      ]),
    ).render(app, size, offset)
