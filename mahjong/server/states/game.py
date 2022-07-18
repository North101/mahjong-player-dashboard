import socket
from typing import Tuple

from mahjong.packets import *
from mahjong.poll import *
from mahjong.shared import *

from .base import *
from .game_draw import *
from .game_ron import *

if TYPE_CHECKING:
  from mahjong.server import Server


class GamePlayer(ClientMixin, GamePlayerMixin):
  def __init__(self, client: socket.socket, points: int, riichi: bool = False):
    self.client = client
    self.points = points
    self.riichi = riichi

  def declare_riichi(self):
    if not self.riichi:
      self.riichi = True
      self.points -= RIICHI_POINTS

  def take_points(self, other: 'GamePlayer', points: int):
    self.points += points
    other.points -= points


GamePlayerTuple = Tuple[
    GamePlayer,
    GamePlayer,
    GamePlayer,
    GamePlayer,
]


class GameServerState(ServerState, GameStateMixin):
  def __init__(
      self, server: 'Server', players: Tuple[socket.socket, socket.socket, socket.socket, socket.socket], starting_points: int = 25000,
      hand: int = 0, repeat: int = 0, bonus_honba=0, bonus_riichi=0, max_rounds: int = 1
  ):
    self.server = server

    self.hand = hand
    self.repeat = repeat
    self.bonus_honba = bonus_honba
    self.bonus_riichi = bonus_riichi
    self.max_rounds = max_rounds

    self.players: GamePlayerTuple = (
        GamePlayer(players[0], starting_points),
        GamePlayer(players[1], starting_points),
        GamePlayer(players[2], starting_points),
        GamePlayer(players[3], starting_points),
    )
    self.update_player_states()

  def on_client_packet(self, client: socket.socket, packet: Packet):
    player = self.player_for_client(client)
    if isinstance(packet, GameRiichiClientPacket):
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

    ron_players = []
    for wind, other_player in self.players_by_wind:
      points: Optional[int]
      if wind == packet.from_wind:
        continue
      elif player == other_player:
        points = packet.points
      else:
        points = None
      ron_players.append(GameRonPlayer(other_player.client, points))

    self.state = GameRonServerState(
        self.server, self, packet.from_wind, ron_players)

  def on_player_ron_complete(self, from_wind: Wind, ron_players: List[GameRonPlayer]):
    winners = [
        (self.player_for_client(player.client), player.points)
        for player in ron_players
    ]
    self.take_riichi_points([
        player
        for (player, _) in winners
    ])

    discarder: GamePlayer = self.player_for_wind(from_wind)
    for (player, points) in winners:
      points = points + (self.total_honba * RON_HONBA_POINTS)
      player.take_points(discarder, points)

    repeat = any((
        self.player_wind(player) == Wind.EAST
        for (player, _) in winners
    ))
    if repeat:
      self.repeat_hand()
    else:
      self.next_hand()

  def on_player_draw(self, player: GamePlayer, packet: GameDrawClientPacket):
    player1, player2, player3, player4 = self.players
    players = (
        GameDrawPlayer(player1.client, packet.tenpai if player ==
                       player1 else None),
        GameDrawPlayer(player2.client, packet.tenpai if player ==
                       player2 else None),
        GameDrawPlayer(player3.client, packet.tenpai if player ==
                       player3 else None),
        GameDrawPlayer(player4.client, packet.tenpai if player ==
                       player4 else None),
    )
    self.state = GameDrawServerState(self.server, self, players)

  def on_player_draw_complete(self, players: DrawPlayerTuple):
    for draw_player in players:
      if not draw_player.tenpai:
        continue

      player = self.player_for_client(draw_player.client)
      for other_player in self.players:
        if player == other_player:
          continue

        player.take_points(other_player, DRAW_POINTS)

    east_index = self.player_index_for_wind(Wind.EAST)
    if players[east_index].tenpai:
      self.repeat_hand(draw=True)
    else:
      self.next_hand(draw=True)

  def take_riichi_points(self, winners: List[GamePlayer]):
    winner = next((
        player
        for _, player in self.players_by_wind
        if player in winners
    ))

    winner.points += (RIICHI_POINTS * self.total_riichi)
    self.bonus_riichi = 0

  def reset_player_riichi(self):
    for player in self.players:
      player.riichi = False

  def repeat_hand(self, draw=False):
    if draw:
      self.bonus_riichi = self.total_riichi
    else:
      self.bonus_riichi = 0

    self.reset_player_riichi()
    self.repeat += 1
    self.update_player_states()

  def next_hand(self, draw=False):
    if draw:
      self.bonus_honba = self.repeat + 1
      self.bonus_riichi = self.total_riichi
    else:
      self.bonus_honba = 0
      self.bonus_riichi = 0

    self.reset_player_riichi()
    self.hand += 1
    self.repeat = 0
    self.update_player_states()

  def player_for_client(self, client: socket.socket):
    return next((
        player
        for player in self.players
        if player.client == client
    ))

  def update_player_states(self):
    for index, player in enumerate(self.players):
      player.send_packet(GameStateServerPacket(
          self.hand,
          self.repeat,
          self.bonus_honba,
          self.bonus_riichi,
          index,
          self.players,
      ))
