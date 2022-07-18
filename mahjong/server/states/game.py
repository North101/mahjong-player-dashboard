import socket
from typing import TYPE_CHECKING, Iterable, List

from mahjong.packets import (GameDrawClientPacket, GameRiichiClientPacket,
                             GameRonClientPacket, GameStateServerPacket,
                             GameTsumoClientPacket, Packet)
from mahjong.shared import (DRAW_POINTS, RIICHI_POINTS, RON_HONBA_POINTS,
                            TSUMO_HONBA_POINTS, GameState)
from mahjong.wind import Wind

from .game_draw import DrawPlayerTuple, GameDrawPlayer, GameDrawServerState
from .game_ron import GameRonPlayer, GameRonServerState, RonPlayerTuple
from .shared import GamePlayer, GamePlayerTuple, ReconnectableGameStateMixin

if TYPE_CHECKING:
  from mahjong.server import Server


class GameServerState(ReconnectableGameStateMixin):
  def __init__(self, server: 'Server', game_state: GameState, players: GamePlayerTuple):
    self.server = server
    self.game_state = game_state
    self.players = players

    self.update_player_states()

  def on_game_reconnect(self, players):
    super().on_game_reconnect(players)

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
        (
            ron_player(player1),
            ron_player(player2),
            ron_player(player3),
            ron_player(player4),
        ),
        packet.from_wind,
        self.on_player_ron_complete,
    )

  def on_player_ron_complete(self, from_wind: Wind, players: RonPlayerTuple):
    self.state = self
    self.players = players

    winners = [
        player
        for player in players
        if player.ron is not None and player.ron > 0
    ]
    self.take_riichi_points(winners)

    discarder: GamePlayer = self.player_for_wind(from_wind)
    for player in winners:
      points = player.ron + (self.total_honba * RON_HONBA_POINTS)
      player.take_points(discarder, points)

    if self.player_for_wind(Wind.EAST) in winners:
      self.repeat_hand()
    else:
      self.next_hand()

  def on_player_draw(self, player: GamePlayer, packet: GameDrawClientPacket):
    def draw_player(p: GamePlayer):
      tenpai = packet.tenpai if p == player else None
      return GameDrawPlayer(p.client, p.points, p.riichi, tenpai)

    player1, player2, player3, player4 = self.players
    players = (
        draw_player(player1),
        draw_player(player2),
        draw_player(player3),
        draw_player(player4),
    )
    self.state = GameDrawServerState(
        self.server,
        self.game_state,
        players,
        self.on_player_draw_complete,
    )

  def on_player_draw_complete(self, players: DrawPlayerTuple):
    self.state = self
    self.players = players

    winners = [
      player
      for player in players
      if player.tenpai == True
    ]
    for player in winners:
      for other_player in self.players:
        if player == other_player:
          continue
        player.take_points(other_player, DRAW_POINTS)

    if self.player_for_wind(Wind.EAST) in winners:
      self.repeat_hand(draw=True)
    else:
      self.next_hand(draw=True)

  def take_riichi_points(self, winners: Iterable[GamePlayer]):
    winner = next((
        player
        for _, player in self.players_by_wind
        if player in winners
    ))

    winner.points += (RIICHI_POINTS * self.total_riichi)
    self.game_state.bonus_riichi = 0

  def reset_player_riichi(self):
    for player in self.players:
      player.riichi = False

  def repeat_hand(self, draw=False):
    if draw:
      self.game_state.bonus_riichi = self.total_riichi
    else:
      self.game_state.bonus_riichi = 0

    self.reset_player_riichi()
    self.game_state.repeat += 1
    self.update_player_states()

  def next_hand(self, draw=False):
    if draw:
      self.game_state.bonus_honba = self.game_state.repeat + 1
      self.game_state.bonus_riichi = self.total_riichi
    else:
      self.game_state.bonus_honba = 0
      self.game_state.bonus_riichi = 0

    self.reset_player_riichi()
    self.game_state.hand += 1
    self.game_state.repeat = 0
    self.update_player_states()

  def player_for_client(self, client: socket.socket):
    try:
      return next((
          player
          for player in self.players
          if player.client == client
      ))
    except StopIteration:
      return None

  def update_player_states(self):
    for index, player in enumerate(self.players):
      player.send_packet(GameStateServerPacket(
          self.game_state, index, self.players))
