from badger_ui.align import Center
from badger_ui.row import Row
from badger_ui.sized import SizedBox
from badger_ui.text import TextWidget

import badger2040w
from badger_ui import App, Offset, Size
from mahjong2040.client import Client
from mahjong2040.packets import RonWindClientPacket
from mahjong2040.shared import Wind

from .shared import GameReconnectClientState


class GameRonWindClientState(GameReconnectClientState):
  def __init__(self, client: 'Client', players: list[int]):
    super().__init__(client)

    self.players = players

  def on_button(self, app: App, pressed: dict[int, bool]) -> bool:
    if pressed[badger2040w.BUTTON_A]:
      self.send_packet(RonWindClientPacket(self.players[-1]))
      return True

    elif pressed[badger2040w.BUTTON_B]:
      self.send_packet(RonWindClientPacket(self.players[-2]))
      return True

    elif pressed[badger2040w.BUTTON_C]:
      self.send_packet(RonWindClientPacket(self.players[-3]))
      return True

    return super().on_button(app, pressed)

  def render(self, app: App, size: Size, offset: Offset):
    super().render(app, size, offset)

    Row(children=[
        SizedBox(
            child=Center(child=TextWidget(
                text=Wind.name(wind),
                line_height=int(30 * 0.8),
                thickness=2,
                scale=0.8,
            )),
            size=Size(size.width // 3, size.height),
        )
        for wind in reversed(self.players)
    ]).render(app, size, offset)
