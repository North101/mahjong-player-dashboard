from mahjong2040.packets import (
    DrawClientPacket,
    DrawServerPacket,
    DrawTenpaiServerPacket,
    Packet,
)
from mahjong2040.shared import DRAW_POINTS, ClientGameState, GameState, Tenpai, Wind

from .shared import BaseGameServerStateMixin, GamePlayer, ServerClient


class GameDrawPlayer(GamePlayer):
  def __init__(self, client: ServerClient, points: int, riichi: bool, tenpai: int):
    super().__init__(client, points, riichi)
    self.tenpai = tenpai


class GameDrawServerState(BaseGameServerStateMixin):
  def __init__(self, server, game_state: GameState[GameDrawPlayer]):
    self.server = server
    self.game_state = game_state

  def init(self):
    for player in self.game_state.players:
      player.send_packet(DrawTenpaiServerPacket(player.tenpai))

  def on_client_packet(self, client: ServerClient, packet: Packet):
    player = self.player_for_client(client)
    if not player:
      return
    elif isinstance(packet, DrawClientPacket):
      self.on_player_draw(player, packet)

  def on_player_draw(self, player: GameDrawPlayer, packet: DrawClientPacket):
    player.tenpai = packet.tenpai
    player.send_packet(DrawTenpaiServerPacket(player.tenpai))

    self.on_player_draw_complete()

  def on_player_draw_complete(self):
    from mahjong2040.server.states.game import GameServerState

    if any((player.tenpai == Tenpai.UNKNOWN for player in self.game_state.players)):
      return

    player_points = tuple((
      player.points
      for player in self.game_state.players
    ))

    tenpai = sum(
        1 if player.tenpai == Tenpai.TENPAI else 0
        for player in self.game_state.players
    )
    noten = len(Wind) - tenpai
    if 0 < tenpai < len(Wind):
      for player in self.game_state.players:
        if player.tenpai == Tenpai.TENPAI:
          player.points += DRAW_POINTS // tenpai
        else:
          player.points -= DRAW_POINTS // noten

    draw_hand = self.game_state.hand
    if self.game_state.player_for_wind(Wind.EAST).tenpai == Tenpai.TENPAI:
      self.repeat_hand(draw=True)
    else:
      self.next_hand(draw=True)
    
    for index, p in enumerate(self.game_state.players):
      p.send_packet(DrawServerPacket(
        game_state=ClientGameState(
          index,
          players=self.game_state.players,
          starting_points=self.game_state.starting_points,
          hand=self.game_state.hand,
          repeat=self.game_state.repeat,
          bonus_honba=self.game_state.bonus_honba,
          bonus_riichi=self.game_state.bonus_riichi,
        ),
        draw_hand=draw_hand,
        tenpai=tuple((
          player.tenpai == Tenpai.TENPAI
          for player in self.game_state.players
        )),
        points=tuple((
          player.points - player_points[i]
          for i, player in enumerate(self.game_state.players)
        )),
      ))

    self.child = GameServerState(self.server, self.game_state)
