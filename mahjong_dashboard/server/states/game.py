import socket
from typing import TYPE_CHECKING

from mahjong_dashboard.packets import (GameDrawClientPacket, GameRiichiClientPacket,
                             GameRonClientPacket, GameStateServerPacket,
                             GameTsumoClientPacket, Packet)
from mahjong_dashboard.shared import TSUMO_HONBA_POINTS, GameState, TenpaiState
from mahjong_dashboard.wind import Wind

from .game_draw import GameDrawPlayer, GameDrawServerState
from .game_ron import GameRonPlayer, GameRonServerState
from .shared import GamePlayer, GamePlayerTuple, BaseGameServerStateMixin

if TYPE_CHECKING:
  from mahjong_dashboard.server import Server


class GameServerState(BaseGameServerStateMixin):
  def __init__(self, server: 'Server', game_state: GameState, players: GamePlayerTuple):
    self.server = server
    self.game_state = game_state
    self.players = players

    self.update_player_states()

  def on_players_reconnect(self, players):
    super().on_players_reconnect(players)

    self.update_player_states()

  def on_client_packet(self, client: socket.socket, packet: Packet):
    player = self.player_for_client(client)
    if not player:
      return
    elif isinstance(packet, GameRiichiClientPacket):
      self.on_player_riichi(player, packet)
    elif isinstance(packet, GameTsumoClientPacket):
      self.on_player_tsumo(player, packet)
    elif isinstance(packet, GameRonClientPacket):
      self.on_player_ron(player, packet)
    elif isinstance(packet, GameDrawClientPacket):
      self.on_player_draw(player, packet)

  def on_player_riichi(self, player: GamePlayer, packet: GameRiichiClientPacket):
    player.declare_riichi()
    self.update_player_states()

  def on_player_tsumo(self, player: GamePlayer, packet: GameTsumoClientPacket):
    self.take_riichi_points([player])

    for other_player in self.players:
      if other_player == player:
        continue

      other_player_wind = self.player_wind(other_player)
      points: int
      if other_player_wind == Wind.EAST:
        points = packet.dealer_points
      else:
        points = packet.points
      points += self.total_honba * TSUMO_HONBA_POINTS
      player.take_points(other_player, points)

    if self.player_wind(player) == Wind.EAST:
      self.repeat_hand()
    else:
      self.next_hand()

  def on_player_ron(self, player: GamePlayer, packet: GameRonClientPacket):
    if self.player_wind(player) == packet.from_wind:
      return

    players_by_wind = {
        player: wind
        for wind, player in self.players_by_wind
    }

    def ron_player(p: GamePlayer):
      if p == player:
        ron = packet.points
      elif players_by_wind[p] == packet.from_wind:
        ron = 0
      else:
        ron = -1

      return GameRonPlayer(p.client, p.points, p.riichi, ron)

    player1, player2, player3, player4 = self.players
    self.state = GameRonServerState(
        self.server,
        self.game_state,
        GamePlayerTuple(
            ron_player(player1),
            ron_player(player2),
            ron_player(player3),
            ron_player(player4),
        ),
        packet.from_wind,
    )

  def on_player_draw(self, player: GamePlayer, packet: GameDrawClientPacket):
    def draw_player(p: GamePlayer):
      tenpai = packet.tenpai if p == player else TenpaiState.unknown
      return GameDrawPlayer(p.client, p.points, p.riichi, tenpai)

    player1, player2, player3, player4 = self.players
    self.state = GameDrawServerState(
        self.server,
        self.game_state,
        GamePlayerTuple(
            draw_player(player1),
            draw_player(player2),
            draw_player(player3),
            draw_player(player4),
        ),
    )

  def update_player_states(self):
    for index, player in enumerate(self.players):
      player.send_packet(GameStateServerPacket(self.game_state, index, self.players))
