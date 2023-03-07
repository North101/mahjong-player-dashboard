from mahjong2040.packets import (
    DrawClientPacket,
    DrawServerPacket,
    GameStateServerPacket,
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
      player.send_packet(DrawServerPacket(player.tenpai))

  def on_players_reconnect(self, clients: list[ServerClient]):
    super().on_players_reconnect(clients)

    for index, player in enumerate(self.game_state.players):
      player.send_packet(GameStateServerPacket(ClientGameState(
          index,
          self.game_state.players,
          self.game_state.hand,
          self.game_state.repeat,
          self.game_state.bonus_honba,
          self.game_state.bonus_riichi,
      )))
      player.send_packet(DrawServerPacket(player.tenpai))

  def on_client_packet(self, client: ServerClient, packet: Packet):
    player = self.player_for_client(client)
    if not player:
      return
    elif isinstance(packet, DrawClientPacket):
      self.on_player_draw(player, packet)

  def on_player_draw(self, player: GameDrawPlayer, packet: DrawClientPacket):
    player.tenpai = packet.tenpai
    player.send_packet(DrawServerPacket(player.tenpai))

    self.on_player_draw_complete()

  def on_player_draw_complete(self):
    from mahjong2040.server.states.game import GameServerState

    if any((player.tenpai == Tenpai.UNKNOWN for player in self.game_state.players)):
      return

    winners = [
        player
        for player in self.game_state.players
        if player.tenpai == True
    ]
    for player in winners:
      for other_player in self.game_state.players:
        if player == other_player:
          continue
        player.take_points(other_player, DRAW_POINTS)

    if self.game_state.player_for_wind(Wind.EAST) in winners:
      self.repeat_hand(draw=True)
    else:
      self.next_hand(draw=True)

    self.child = GameServerState(self.server, self.game_state)
