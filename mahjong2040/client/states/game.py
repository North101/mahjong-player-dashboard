from badger_ui.align import Bottom, Center, Left, Right, Top
from badger_ui.base import App, Offset, Size, Widget
from badger_ui.column import Column
from badger_ui.padding import EdgeOffsets, Padding
from badger_ui.row import Row
from badger_ui.text import TextWidget
from mahjong2040.packets import GameStateServerPacket, Packet, RiichiClientPacket
from mahjong2040.shared import ClientGameState, GamePlayerMixin, Wind

import badger2040w

from .game_menu import GameMenuClientState
from .shared import GameReconnectClientState


class GameClientState(GameReconnectClientState):
  player_size = Size(115, 30)
  round_size = Size(40, 8)

  def __init__(self, client, game_state: ClientGameState):
    super().__init__(client)

    self.game_state = game_state
  
  @property
  def round_text(self):
    return f'{Wind.name(self.game_state.round)[0].upper()}{self.game_state.hand + 1}'

  def on_server_packet(self, packet: Packet) -> bool:
    if isinstance(packet, GameStateServerPacket):
      self.game_state = packet.game_state
      return True

    return super().on_server_packet(packet)

  def on_button(self, app: App, pressed: dict[int, bool]) -> bool:
    if pressed[badger2040w.BUTTON_B]:
      app.child = GameMenuClientState(self.client, self.game_state)
      return True

    elif pressed[badger2040w.BUTTON_UP]:
      self.send_packet(RiichiClientPacket())
      return True

    elif pressed[badger2040w.BUTTON_DOWN]:
      # toggle scores
      pass

    return super().on_button(app, pressed)

  def render(self, app: App, size: Size, offset: Offset):
    super().render(app, size, offset)

    (wind1, player1), (wind2, player2), (wind3, player3), (wind4, player4) = self.game_state.players_from_me

    Bottom(child=Center(child=PlayerWidget(
        player=player1,
        wind=wind1,
    ))).render(app, size, offset)
    Right(child=Center(child=PlayerWidget(
        player=player2,
        wind=wind2,
    ))).render(app, size, offset)
    Top(child=Center(child=PlayerWidget(
        player=player3,
        wind=wind3,
    ))).render(app, size, offset)
    Left(child=Center(child=PlayerWidget(
        player=player4,
        wind=wind4,
    ))).render(app, size, offset)

    Center(child=TextWidget(
      text=self.round_text,
      line_height=30,
      thickness=2,
    )).render(app, size, offset)


class RiichiWidget(Widget):
  size = Size(40, 8)

  def __init__(self, riichi):
    self.riichi = riichi
  
  def measure(self, app: 'App', size: Size) -> Size:
    return self.size

  def render(self, app: 'App', size: Size, offset: Offset):
    if not self.riichi:
      return

    width = size.width
    height = size.height
    start_x = offset.x
    start_y = offset.y
    end_x = start_x + width
    end_y = start_y + height

    app.display.set_pen(0)
    app.display.rectangle(
        start_x,
        start_y,
        2,
        height,
    )
    app.display.rectangle(
        start_x,
        start_y,
        width,
        2,
    )
    app.display.rectangle(
        end_x,
        start_y,
        2,
        height,
    )
    app.display.rectangle(
        start_x,
        end_y,
        width,
        2,
    )

    dot_size = 4
    app.display.rectangle(
        start_x + ((width - dot_size) // 2),
        start_y + ((height - dot_size) // 2) + 1,
        dot_size,
        dot_size,
    )


class PlayerWidget(Widget):
  size = Size(115, 40)

  def __init__(self, player: GamePlayerMixin, wind: int):
    self.player = player
    self.wind = wind
  
  def measure(self, app: 'App', size: Size) -> Size:
    return self.size
  
  def render(self, app: 'App', size: Size, offset: Offset):
    Padding(
      padding=EdgeOffsets(bottom=1),
      child=Column(children=[
        Row(children=[
          TextWidget(
              text=Wind.name(self.wind)[0].upper(),
              line_height=30,
              font='sans',
              thickness=2,
              scale=0.6,
          ),
          TextWidget(
              text=f'{self.player.points * 100}',
              line_height=30,
              font='sans',
              thickness=2,
              scale=1,
          ),
        ]),
        RiichiWidget(self.player.riichi),
      ]),
    ).render(app, size, offset)
