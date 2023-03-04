import network
from badger_ui.align import Bottom, Center
from badger_ui.column import Column
from badger_ui.text import TextWidget
from mahjong2040.packets import (
    LobbyPlayersServerPacket,
    Packet,
    SetupPlayerWindServerPacket,
)

from badger_ui import App, Offset, Size

from .base import ClientState
from .setup_player_wind import SetupPlayerWindClientState


class LobbyClientState(ClientState):
  def __init__(self, client, count: tuple[int, int] | None = None):
    super().__init__(client)

    self.count = count

  def ip_address(self):
    return network.WLAN(network.STA_IF).ifconfig()[0]

  def on_server_packet(self, packet: Packet) -> bool:
    if isinstance(packet, LobbyPlayersServerPacket):
      self.count = (packet.count, packet.max_players)
      return True

    elif isinstance(packet, SetupPlayerWindServerPacket):
      self.child = SetupPlayerWindClientState(self.client, packet.wind)
      return True

    return super().on_server_packet(packet)

  def render(self, app: App, size: Size, offset: Offset):
    super().render(app, size, offset)

    if self.count is None:
      Center(child=TextWidget(
          text='Connecting...',
          line_height=24,
          thickness=2,
          scale=0.8,
      )).render(app, size, offset)
      return

    current, max_players = self.count
    Center(child=Column(children=[
        TextWidget(
            text='Waiting...',
            line_height=24,
            thickness=2,
            scale=0.8,
        ),
        TextWidget(
            text=f'{current} / {max_players}',
            line_height=24,
            thickness=2,
            scale=0.8,
        ),
    ])).render(app, size, offset)

    Bottom(child=Center(child=TextWidget(
      text=f'IP: {self.ip_address()}',
      line_height=15,
      font='sans',
      thickness=2,
      scale=0.5,
    ))).render(app, size, offset)
