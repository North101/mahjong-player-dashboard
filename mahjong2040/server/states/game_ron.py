from mahjong2040.packets import (
    GameStateServerPacket,
    Packet,
    RonScoreClientPacket,
    RonScoreServerPacket,
    RonWindServerPacket,
)
from mahjong2040.shared import RON_HONBA_POINTS, ClientGameState, GameState, Wind

from .shared import BaseGameServerStateMixin, GamePlayer, ServerClient


class GameRonPlayer(GamePlayer):
  def __init__(self, client: ServerClient, points: int, riichi: bool, ron: int):
    super().__init__(client, points, riichi)
    self.ron = ron


class GameRonServerState(BaseGameServerStateMixin):
  def __init__(
      self,
      server,
      game_state: GameState[GameRonPlayer],
      from_wind: int,
  ):
    self.server = server
    self.game_state = game_state
    self.from_wind = from_wind

    for player in game_state.players:
      if player.ron >= 0:
        continue
      player.send_packet(RonWindServerPacket(from_wind))

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
      if player.ron >= 0:
        continue
      player.send_packet(RonWindServerPacket(self.from_wind))

  def on_client_packet(self, client: ServerClient, packet: Packet):
    player = self.player_for_client(client)
    if not player:
      return
    elif isinstance(packet, RonScoreClientPacket):
      self.on_player_ron(player, packet)

  def on_player_ron(self, player: GameRonPlayer, packet: RonScoreClientPacket):
    player.ron = packet.points
    player.send_packet(RonScoreServerPacket(self.from_wind, packet.points))
    self.on_player_ron_complete()

  def on_player_ron_complete(self):
    from mahjong2040.server.states.game import GameServerState

    if any((player.ron < 0 for player in self.game_state.players)):
      return

    winners = [
        player
        for player in self.game_state.players
        if player.ron > 0
    ]
    if not winners:
      self.child = GameServerState(self.server, self.game_state)
      return

    self.take_riichi_points(winners)
    discarder = self.game_state.player_for_wind(self.from_wind)
    for player in winners:
      points = player.ron + (self.game_state.total_honba * RON_HONBA_POINTS)
      player.take_points(discarder, points)

    if self.game_state.player_for_wind(Wind.EAST) in winners:
      self.repeat_hand()
    else:
      self.next_hand()

    self.child = GameServerState(self.server, self.game_state)
