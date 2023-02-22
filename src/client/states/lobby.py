import socket

from badger_ui.align import Center
from badger_ui.column import Column
from badger_ui.text import TextWidget
from mahjong2040.packets import (LobbyPlayersServerPacket, Packet,
                                 SelectWindServerPacket)

from badger_ui import App, Offset, Size

from .base import ClientState
from .select_wind import SelectWindClientState


class LobbyClientState(ClientState):
  def __init__(self, client, count: tuple[int, int] | None = None):
    super().__init__(client)

    self.count = count

  def on_server_packet(self, server: socket.socket, packet: Packet):
    print(packet.__class__.__name__, packet.__repr__())
    if isinstance(packet, LobbyPlayersServerPacket):
      self.count = (packet.count, packet.max_players)

    elif isinstance(packet, SelectWindServerPacket):
      self.child = SelectWindClientState(self.client, packet.wind)

  def render(self, app: App, size: Size, offset: Offset):
    if self.count is None:
      Center(child=TextWidget(
          text='Connecting...',
          line_height=30,
          thickness=2,
      )).render(app, size, offset)
      return

    current, max_players = self.count
    Center(child=Column(children=[
        TextWidget(
            text='Waiting...',
            line_height=30,
            thickness=2,
        ),
        TextWidget(
            text=f'{current} / {max_players}',
            line_height=30,
            thickness=2,
        ),
    ])).render(app, size, offset)
