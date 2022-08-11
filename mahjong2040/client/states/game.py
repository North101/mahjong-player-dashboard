import socket

import badger2040
from badger_ui import App, Offset, Size
from badger_ui.align import Center
from badger_ui.row import Row
from badger_ui.text import TextWidget
from mahjong2040.packets import (DrawServerPacket, GameStateServerPacket,
                                 Packet, RiichiClientPacket, RonServerPacket)
from mahjong2040.shared import (ClientGameState, GamePlayerMixin, GameState,
                                Wind)

from .draw import DrawClientState
from .ron_score import RonScoreClientState
from .ron_wind import RonWindClientState
from .shared import GameReconnectClientState
from .tsumo_dealer import TsumoDealerClientState
from .tsumo_nondealer import TsumoNonDealerClientState


class GameClientState(GameReconnectClientState):
  player_size = Size(115, 30)

  def __init__(self, client, game_state: ClientGameState):
    self.client = client

    self.game_state = game_state

  def on_server_packet(self, server: socket.socket, packet: Packet):
    super().on_server_packet(server, packet)

    if isinstance(packet, GameStateServerPacket):
      self.game_state = packet.game_state

    elif isinstance(packet, DrawServerPacket):
      self.child = DrawClientState(self.client)

    elif isinstance(packet, RonServerPacket):
      self.child = RonScoreClientState(self.client, packet.from_wind)

  def on_button(self, app: App, pressed: dict[int, bool]) -> bool:
    if pressed[badger2040.BUTTON_A]:
      if self.game_state.player_wind(self.game_state.me) == 0:
        app.child = TsumoNonDealerClientState(self.client, 0)
      else:
        app.child = TsumoDealerClientState(self.client)
      return True

    elif pressed[badger2040.BUTTON_B]:
      app.child = RonWindClientState(self.client, [
          wind
          for wind, player in self.game_state.players_from_me
          if player != self.game_state.me
      ])
      return True

    elif pressed[badger2040.BUTTON_C]:
      app.child = DrawClientState(self.client)
      return True

    elif pressed[badger2040.BUTTON_UP]:
      self.send_packet(RiichiClientPacket())
      return True

    elif pressed[badger2040.BUTTON_DOWN]:
      # toggle scores
      pass

    return super().on_button(app, pressed)

  def render(self, app: App, size: Size, offset: Offset):
    (wind1, player1), (wind2, player2), (wind3, player3), (wind4, player4) = self.game_state.players_from_me

    player_widget(
        app=app,
        size=self.player_size,
        offset=Offset((size.width - self.player_size.width) // 2, size.height - self.player_size.height),
        player=player1,
        wind=wind1,
    )
    if player1.riichi:
      riichi_widget(app, Size(40, 8), Offset((size.width - 40) // 2, (size.height + 40) // 2))

    player_widget(
        app=app,
        size=self.player_size,
        offset=Offset(size.width - self.player_size.width, (128 - self.player_size.height) // 2),
        player=player2,
        wind=wind2,
    )
    if player2.riichi:
      riichi_widget(app, Size(8, 40), Offset((size.width + 40) // 2, (size.height - 40) // 2))

    player_widget(
        app=app,
        size=self.player_size,
        offset=Offset((size.width - self.player_size.width) // 2, 0),
        player=player3,
        wind=wind3,
    )
    if player3.riichi:
      riichi_widget(app, Size(40, 8), Offset((size.width - 40) // 2, ((size.height - 40) // 2) - 8))

    player_widget(
        app=app,
        size=self.player_size,
        offset=Offset(0, (128 - self.player_size.height) // 2),
        player=player4,
        wind=wind4,
    )
    if player4.riichi:
      riichi_widget(app, Size(8, 40), Offset(((size.width - 40) // 2) - 8, (size.height - 40) // 2))

    round_widget(
        app=app,
        size=Size(40, 40),
        offset=Offset((size.width - 40) // 2, (size.height - 40) // 2),
        game_state=self.game_state,
    )


def round_widget(app: App, size: Size, offset: Offset, game_state: GameState):
  round_text = f'{Wind.name(game_state.round)[0].upper()}{game_state.hand + 1}'

  width = size.width
  height = size.height
  start_x = offset.x
  start_y = offset.y
  end_x = start_x + width
  end_y = start_y + height

  app.display.pen(0)
  app.display.line(
      start_x,
      start_y,
      start_x,
      end_y,
  )
  app.display.line(
      start_x,
      start_y,
      end_x,
      start_y,
  )
  app.display.line(
      end_x,
      start_y,
      end_x,
      end_y,
  )
  app.display.line(
      start_x,
      end_y,
      end_x,
      end_y,
  )

  round_width = app.display.measure_text(round_text)
  app.display.text(
      round_text,
      offset.x + (width // 2) - (round_width // 2),
      offset.y + (height // 2),
  )


def riichi_widget(app: App, size: Size, offset: Offset):
  width = size.width
  height = size.height
  start_x = offset.x
  start_y = offset.y
  end_x = start_x + width
  end_y = start_y + height

  app.display.pen(0)
  app.display.line(
      start_x,
      start_y,
      start_x,
      end_y,
  )
  app.display.line(
      start_x,
      start_y,
      end_x,
      start_y,
  )
  app.display.line(
      end_x,
      start_y,
      end_x,
      end_y,
  )
  app.display.line(
      start_x,
      end_y,
      end_x,
      end_y,
  )

  dot_size = 2
  app.display.rectangle(
      start_x + ((width - dot_size) // 2),
      start_y + ((height - dot_size) // 2),
      dot_size,
      dot_size,
  )


def player_widget(app: App, size: Size, offset: Offset, player: GamePlayerMixin, wind: int):
  Center(child=Row(
      children=[
          TextWidget(
              text=Wind.name(wind)[0].upper(),
              font='sans',
              thickness=2,
              scale=0.6,
              line_height=size.height,
          ),
          TextWidget(
              text=str(player.points),
              font='sans',
              thickness=2,
              color=0,
              scale=1,
              line_height=size.height,
          ),
      ],
  )).render(app, size, offset)
