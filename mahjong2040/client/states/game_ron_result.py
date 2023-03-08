from badger_ui.align import Bottom, Center, Left, Right, Top
from badger_ui.base import App, Offset, Size
from badger_ui.padding import EdgeOffsets, Padding

import badger2040w
from mahjong2040.client import Client
from mahjong2040.packets import GameStateServerPacket, Packet, RonServerPacket
from mahjong2040.shared import Wind

from .shared import GameReconnectClientState
from .widgets.arrow import ArrowWidget, Direction
from .widgets.player import PlayerWidget


class RonResultClientState(GameReconnectClientState):
  def __init__(self, client: 'Client', packet: RonServerPacket):
    super().__init__(client)

    self.packet = packet
    self.game_state = packet.game_state

  @property
  def from_player(self):
    return (self.packet.ron_wind - self.game_state.player_index + self.packet.ron_hand) % len(Wind)

  @property
  def players_from_me(self):
    for i in range(len(Wind)):
      player_wind = (i + self.game_state.player_index - self.packet.ron_hand) % len(Wind)
      if player_wind == self.packet.ron_wind:
        points = -(self.packet.player1_points + self.packet.player2_points + self.packet.player3_points)
      elif player_wind == ((self.packet.ron_wind + 1) % len(Wind)):
        points = self.packet.player1_points
      elif player_wind == ((self.packet.ron_wind + 2) % len(Wind)):
        points = self.packet.player2_points
      elif player_wind == ((self.packet.ron_wind + 3) % len(Wind)):
        points = self.packet.player3_points
      else:
        points = 0

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

    if player0 != 0:
      Bottom(child=Center(child=PlayerWidget(
          points=player0,
          wind=wind0,
          absolute=False,
      ))).render(app, size, offset)
    if player1 != 0:
      Right(child=Center(child=PlayerWidget(
          points=player1,
          wind=wind1,
          absolute=False,
      ))).render(app, size, offset)
    if player2 != 0:
      Top(child=Center(child=PlayerWidget(
          points=player2,
          wind=wind2,
          absolute=False,
      ))).render(app, size, offset)
    if player3 != 0:
      Left(child=Center(child=PlayerWidget(
          points=player3,
          wind=wind3,
          absolute=False,
      ))).render(app, size, offset)

    from_player = self.from_player
    if from_player == 0:
      if player1 != 0:
        Bottom(child=Right(child=Padding(
          padding=EdgeOffsets(right=20),
          child=ArrowWidget(
            arrow=Direction.UP,
            lines=Direction.UP | Direction.LEFT,
          ),
        ))).render(app, size, offset)
      if player2 != 0:
        Center(child=ArrowWidget(
          arrow=Direction.UP,
          lines=Direction.UP | Direction.DOWN,
        )).render(app, size, offset)
      if player3 != 0:
        Bottom(child=Left(child=Padding(
          padding=EdgeOffsets(left=20),
          child=ArrowWidget(
            arrow=Direction.UP,
            lines=Direction.UP | Direction.RIGHT,
          ),
        ))).render(app, size, offset)

    elif from_player == 1:
      if player2 != 0:
        Top(child=Right(child=Padding(
          padding=EdgeOffsets(right=20),
          child=ArrowWidget(
            arrow=Direction.LEFT,
            lines=Direction.LEFT | Direction.DOWN,
          ),
        ))).render(app, size, offset)
      if player3 != 0:
        Center(child=ArrowWidget(
          arrow=Direction.LEFT,
          lines=Direction.LEFT | Direction.RIGHT,
        )).render(app, size, offset)
      if player0 != 0:
        Bottom(child=Right(child=Padding(
          padding=EdgeOffsets(right=20),
          child=ArrowWidget(
            arrow=Direction.LEFT,
            lines=Direction.LEFT | Direction.UP,
          ),
        ))).render(app, size, offset)

    elif from_player == 2:
      if player3 != 0:
        Top(child=Left(child=Padding(
          padding=EdgeOffsets(left=20),
          child=ArrowWidget(
            arrow=Direction.DOWN,
            lines=Direction.DOWN | Direction.RIGHT,
          ),
        ))).render(app, size, offset)
      if player0 != 0:
        Center(child=ArrowWidget(
          arrow=Direction.DOWN,
          lines=Direction.DOWN | Direction.UP,
        )).render(app, size, offset)
      if player1 != 0:
        Top(child=Right(child=Padding(
          padding=EdgeOffsets(right=20),
          child=ArrowWidget(
            arrow=Direction.DOWN,
            lines=Direction.DOWN | Direction.LEFT,
          ),
        ))).render(app, size, offset)

    elif from_player == 3:
      if player0 != 0:
        Bottom(child=Left(child=Padding(
          padding=EdgeOffsets(left=20),
          child=ArrowWidget(
            arrow=Direction.RIGHT,
            lines=Direction.RIGHT | Direction.UP,
          ),
        ))).render(app, size, offset)
      if player1 != 0:
        Center(child=ArrowWidget(
          arrow=Direction.RIGHT,
          lines=Direction.RIGHT | Direction.LEFT,
        )).render(app, size, offset)
      if player2 != 0:
        Top(child=Left(child=Padding(
          padding=EdgeOffsets(left=20),
          child=ArrowWidget(
            arrow=Direction.RIGHT,
            lines=Direction.RIGHT | Direction.DOWN,
          ),
        ))).render(app, size, offset)
