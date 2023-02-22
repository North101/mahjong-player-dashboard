import socket

import badger2040w
from badger_ui.align import Center
from badger_ui.text import TextWidget
from mahjong2040.client.widgets.score_input import ScoreInputWidget
from mahjong2040.packets import (DrawServerPacket, GameStateServerPacket,
                                 Packet, RonServerPacket)

from badger_ui import App, Offset, Size

from .draw import DrawClientState
from .ron_score import RonScoreClientState
from .shared import GameReconnectClientState
from .tsumo_nondealer import TsumoNonDealerClientState


class TsumoDealerClientState(GameReconnectClientState):
  def __init__(self, client):
    super().__init__(client)

    self.score = ScoreInputWidget()

  def on_server_packet(self, server: socket.socket, packet: Packet):
    from .game import GameClientState

    super().on_server_packet(server, packet)
    if isinstance(packet, GameStateServerPacket):
      self.child = GameClientState(self.client, packet.game_state)

    elif isinstance(packet, RonServerPacket):
      self.child = RonScoreClientState(self.client, packet.from_wind)

    elif isinstance(packet, DrawServerPacket):
      self.child = DrawClientState(self.client)

  def on_button(self, app: App, pressed: dict[int, bool]) -> bool:
    if pressed[badger2040w.BUTTON_B]:
      app.child = TsumoNonDealerClientState(self.client, self.score.to_value)
      return True

    return self.score.on_button(app, pressed)

  def render(self, app: App, size: Size, offset: Offset):
    Center(child=TextWidget(
        text='Dealer',
        line_height=24,
        thickness=2,
        scale=0.8,
    )).render(app, Size(size.width, 24), offset)
    self.score.render(app, size, offset)
