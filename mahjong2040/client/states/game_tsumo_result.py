from badger_ui.align import Bottom, Center, Left, Right, Top
from badger_ui.base import App, Offset, Size, Widget
from badger_ui.padding import EdgeOffsets, Padding
from badger_ui.row import Row
from badger_ui.text import TextWidget

import badger2040w
from mahjong2040.packets import GameStateServerPacket, Packet, TsumoServerPacket
from mahjong2040.shared import IntEnum, Wind

from .shared import GameReconnectClientState


class TsumoResultClientState(GameReconnectClientState):
  def __init__(self, client, packet: TsumoServerPacket):
    super().__init__(client)

    self.packet = packet
    self.game_state = packet.game_state

  @property
  def winning_player(self):
    return (self.packet.tsumo_wind - self.game_state.player_index + self.packet.tsumo_hand) % len(Wind)

  @property
  def players_from_me(self):
    for i in range(len(Wind)):
      player_wind = (i + self.game_state.player_index - self.packet.tsumo_hand) % len(Wind)
      dealer_tsumo = self.packet.tsumo_wind == Wind.EAST
      player_is_dealer = player_wind == Wind.EAST
      player_is_winner = player_wind == self.packet.tsumo_wind
      if player_is_winner:
        if player_is_dealer:
          points = self.packet.dealer_points * 3
        else:
          points = self.packet.dealer_points + (self.packet.nondealer_points * 2)
      else:
        if dealer_tsumo or player_is_dealer:
          points = -self.packet.dealer_points
        else:
          points = -self.packet.nondealer_points

      yield player_wind, points

  def on_server_packet(self, packet: Packet) -> bool:
    if isinstance(packet, GameStateServerPacket):
      self.game_state = packet.game_state
      return True

    return super().on_server_packet(packet)

  def on_button(self, app: App, pressed: dict[int, bool]) -> bool:
    if pressed[badger2040w.BUTTON_B]:
      from .game import GameClientState
      self.child = GameClientState(self.client, self.game_state)
      return True

    return super().on_button(app, pressed)

  def render(self, app: App, size: Size, offset: Offset):
    super().render(app, size, offset)

    (wind0, player0), (wind1, player1), (wind2, player2), (wind3, player3) = self.players_from_me

    Bottom(child=Center(child=PlayerWidget(
        points=player0,
        wind=wind0,
    ))).render(app, size, offset)
    Right(child=Center(child=PlayerWidget(
        points=player1,
        wind=wind1,
    ))).render(app, size, offset)
    Top(child=Center(child=PlayerWidget(
        points=player2,
        wind=wind2,
    ))).render(app, size, offset)
    Left(child=Center(child=PlayerWidget(
        points=player3,
        wind=wind3,
    ))).render(app, size, offset)

    winning_player = self.winning_player
    if winning_player == 0:
      Bottom(child=Left(child=Padding(
        padding=EdgeOffsets(left=20),
        child=ArrowWidget(
          arrow=Direction.RIGHT,
          lines=Direction.UP | Direction.RIGHT,
        ),
      ))).render(app, size, offset)
      Center(child=ArrowWidget(
        arrow=Direction.DOWN,
        lines=Direction.UP | Direction.DOWN,
      )).render(app, size, offset)
      Bottom(child=Right(child=Padding(
        padding=EdgeOffsets(right=20),
        child=ArrowWidget(
          arrow=Direction.LEFT,
          lines=Direction.UP | Direction.LEFT,
        ),
      ))).render(app, size, offset)

    elif winning_player == 1:
      Bottom(child=Right(child=Padding(
        padding=EdgeOffsets(right=20),
        child=ArrowWidget(
          arrow=Direction.UP,
          lines=Direction.LEFT | Direction.UP,
        ),
      ))).render(app, size, offset)
      Center(child=ArrowWidget(
        arrow=Direction.RIGHT,
        lines=Direction.LEFT | Direction.RIGHT,
      )).render(app, size, offset)
      Top(child=Right(child=Padding(
        padding=EdgeOffsets(right=20),
        child=ArrowWidget(
          arrow=Direction.DOWN,
          lines=Direction.LEFT | Direction.DOWN,
        ),
      ))).render(app, size, offset)

    elif winning_player == 2:
      Top(child=Right(child=Padding(
        padding=EdgeOffsets(right=20),
        child=ArrowWidget(
          arrow=Direction.LEFT,
          lines=Direction.DOWN | Direction.LEFT,
        ),
      ))).render(app, size, offset)
      Center(child=ArrowWidget(
        arrow=Direction.UP,
        lines=Direction.DOWN | Direction.UP,
      )).render(app, size, offset)
      Top(child=Left(child=Padding(
        padding=EdgeOffsets(left=20),
        child=ArrowWidget(
          arrow=Direction.RIGHT,
          lines=Direction.DOWN | Direction.RIGHT,
        ),
      ))).render(app, size, offset)

    elif winning_player == 3:
      Top(child=Left(child=Padding(
        padding=EdgeOffsets(left=20),
        child=ArrowWidget(
          arrow=Direction.DOWN,
          lines=Direction.RIGHT | Direction.DOWN,
        ),
      ))).render(app, size, offset)
      Center(child=ArrowWidget(
        arrow=Direction.LEFT,
        lines=Direction.RIGHT | Direction.LEFT,
      )).render(app, size, offset)
      Bottom(child=Left(child=Padding(
        padding=EdgeOffsets(left=20),
        child=ArrowWidget(
          arrow=Direction.UP,
          lines=Direction.RIGHT | Direction.UP,
        ),
      ))).render(app, size, offset)


class PlayerWidget(Widget):
  height = 40
  font = 'sans'
  thickness = 2
  points_scale = 0.8
  wind_scale = 0.6

  def __init__(self, points: int, wind: int):
    self.points = points
    self.wind = wind
  
  def points_text(self):
    return f'{"+" if self.points >= 0 else ""}{self.points * 100}'
  
  def wind_text(self):
    return Wind.name(self.wind)[0].upper()

  def width(self, app: App):
    app.display.set_font(self.font)
    app.display.set_thickness(self.thickness)
    points_width = app.display.measure_text(self.points_text(), scale=self.points_scale)
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
            scale=self.points_scale,
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


class DirectionState(IntEnum):
  LEFT = 1
  UP = 2
  RIGHT = 4
  DOWN = 8


Direction = DirectionState()


class ArrowWidget(Widget):
  size = Size(60, 40)

  def __init__(self, arrow: Direction, lines: int):
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
  
  def draw_line(self, app: 'App', size: Size, offset: Offset, direction: Direction):
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
