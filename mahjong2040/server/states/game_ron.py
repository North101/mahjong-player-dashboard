import socket

from mahjong2040.packets import (GameStateServerPacket, Packet,
                                 RonClientPacket, RonServerPacket)
from mahjong2040.shared import (RON_HONBA_POINTS, ClientGameState, GameState,
                                Wind)

from .shared import BaseGameServerStateMixin, GamePlayer


class GameRonPlayer(GamePlayer):
  def __init__(self, client: socket.socket, points: int, riichi: bool, ron: int):
    self.client = client
    self.points = points
    self.riichi = riichi
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
      player.send_packet(RonServerPacket(from_wind))

  def on_players_reconnect(self, clients: list[socket.socket]):
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
      player.send_packet(RonServerPacket(self.from_wind))

  def on_client_packet(self, client: socket.socket, packet: Packet):
    player = self.player_for_client(client)
    if not player:
      return
    elif isinstance(packet, RonClientPacket):
      self.on_player_ron(player, packet)

  def on_player_ron(self, player: GameRonPlayer, packet: RonClientPacket):
    player.ron = packet.points
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
    self.take_riichi_points(winners)

    discarder: GamePlayer = self.game_state.player_for_wind(self.from_wind)
    for player in winners:
      points = player.ron + (self.game_state.total_honba * RON_HONBA_POINTS)
      player.take_points(discarder, points)

    if self.game_state.player_for_wind(Wind.EAST) in winners:
      self.repeat_hand()
    else:
      self.next_hand()

    self.child = GameServerState(self.server, self.game_state)
