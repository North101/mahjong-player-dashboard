import socket
from typing import TYPE_CHECKING

from mahjong_dashboard.packets import GameRonClientPacket, GameRonServerPacket, GameStateServerPacket, Packet
from mahjong_dashboard.shared import RON_HONBA_POINTS, GamePlayerTuple, GameState
from mahjong_dashboard.wind import Wind

from .shared import ClientList, GamePlayer, BaseGameServerStateMixin

if TYPE_CHECKING:
  from mahjong_dashboard.server import Server


class GameRonPlayer(GamePlayer):
  def __init__(self, client: socket.socket, points: int, riichi: bool, ron: int):
    self.client = client
    self.points = points
    self.riichi = riichi
    self.ron = ron


class GameRonServerState(BaseGameServerStateMixin[GameRonPlayer]):
  def __init__(self, server: 'Server', game_state: GameState, players: GamePlayerTuple[GameRonPlayer],
               from_wind: Wind):
    self.server = server
    self.game_state = game_state
    self.players = players
    self.from_wind = from_wind

    for player in players:
      if player.ron >= 0:
        continue
      player.send_packet(GameRonServerPacket(from_wind))

  def on_players_reconnect(self, clients: ClientList):
    super().on_players_reconnect(clients)

    for index, player in enumerate(self.players):
      player.send_packet(GameStateServerPacket(self.game_state, index, self.players))
      if player.ron >= 0:
        continue
      player.send_packet(GameRonServerPacket(self.from_wind))

  def on_client_packet(self, client: socket.socket, packet: Packet):
    player = self.player_for_client(client)
    if not player:
      return
    elif isinstance(packet, GameRonClientPacket):
      self.on_player_ron(player, packet)

  def on_player_ron(self, player: GameRonPlayer, packet: GameRonClientPacket):
    player.ron = packet.points
    self.on_player_ron_complete()

  def on_player_ron_complete(self):
    from mahjong_dashboard.server.states.game import GameServerState

    if any((player.ron < 0 for player in self.players)):
      return

    winners = [
        player
        for player in self.players
        if player.ron > 0
    ]
    self.take_riichi_points(winners)

    discarder: GamePlayer = self.player_for_wind(self.from_wind)
    for player in winners:
      points = player.ron + (self.total_honba * RON_HONBA_POINTS)
      player.take_points(discarder, points)

    if self.player_for_wind(Wind.EAST) in winners:
      self.repeat_hand()
    else:
      self.next_hand()

    self.state = GameServerState(self.server, self.game_state, self.players)
