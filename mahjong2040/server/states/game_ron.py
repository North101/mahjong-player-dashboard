from mahjong2040 import score_calculator
from mahjong2040.packets import (
    Packet,
    RonScoreClientPacket,
    RonScoreServerPacket,
    RonServerPacket,
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

  def init(self):
    for wind, player in self.game_state.players_by_wind:
      if player.ron >= 0:
        continue
      player.send_packet(RonWindServerPacket(self.from_wind, wind == Wind.EAST))

  def on_client_packet(self, client: ServerClient, packet: Packet):
    player = self.player_for_client(client)
    if not player:
      return
    elif isinstance(packet, RonScoreClientPacket):
      self.on_player_ron(player, packet)

  def on_player_ron(self, player: GameRonPlayer, packet: RonScoreClientPacket):
    is_dealer = self.game_state.player_wind(player) == Wind.EAST
    player.ron = score_calculator.ron(packet.han, packet.fu_index, is_dealer)
    player.send_packet(RonScoreServerPacket(self.from_wind, player.ron))
    self.on_player_ron_complete()

  def on_player_ron_complete(self):
    from mahjong2040.server.states.game import GameServerState

    if any((player.ron < 0 for player in self.game_state.players)):
      return

    player_points = tuple((
        player.points
        for player in self.game_state.players
    ))

    winners = [
        player
        for player in self.game_state.players
        if player.ron > 0
    ]
    if not winners:
      self.child = GameServerState(self.server, self.game_state)
      return

    self.distribute_riichi_points(winners)
    from_player = self.game_state.player_for_wind(self.from_wind)
    honba_points = self.game_state.total_honba * RON_HONBA_POINTS
    for player in winners:
      points = player.ron + honba_points
      player.take_points(from_player, points)

    hand = self.game_state.hand
    if self.game_state.player_for_wind(Wind.EAST) in winners:
      self.repeat_hand()
    else:
      self.next_hand()

    for index, p in enumerate(self.game_state.players):
      p.send_packet(RonServerPacket(
          game_state=ClientGameState(
              index,
              players=self.game_state.players,
              starting_points=self.game_state.starting_points,
              hand=self.game_state.hand,
              repeat=self.game_state.repeat,
              bonus_honba=self.game_state.bonus_honba,
              bonus_riichi=self.game_state.bonus_riichi,
          ),
          ron_wind=self.from_wind,
          ron_hand=hand,
          points=tuple((
              player.points - player_points[i]
              for i, player in enumerate(self.game_state.players)
          )),
      ))

    self.child = GameServerState(self.server, self.game_state)
