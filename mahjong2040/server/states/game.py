from mahjong2040 import score_calculator
from mahjong2040.packets import (
    DrawClientPacket,
    GameStateServerPacket,
    Packet,
    RedrawClientPacket,
    RiichiClientPacket,
    RonWindClientPacket,
    TsumoClientPacket,
    TsumoServerPacket,
)
from mahjong2040.server.states.base import GamePlayer
from mahjong2040.shared import (
    TSUMO_HONBA_POINTS,
    ClientGameState,
    GameState,
    Tenpai,
    Wind,
)

from .shared import BaseGameServerStateMixin, ServerClient


class GameServerState(BaseGameServerStateMixin):
  def __init__(self, server, game_state: GameState[GamePlayer]):
    self.server = server
    self.game_state = game_state

  def init(self):
    self.update_player_states()

  def on_client_packet(self, client: ServerClient, packet: Packet):
    player = self.player_for_client(client)
    if not player:
      return
    elif isinstance(packet, RiichiClientPacket):
      self.on_player_riichi(player)
    elif isinstance(packet, TsumoClientPacket):
      self.on_player_tsumo(player, packet)
    elif isinstance(packet, RonWindClientPacket):
      self.on_player_ron(player, packet)
    elif isinstance(packet, DrawClientPacket):
      self.on_player_draw(player, packet)
    elif isinstance(packet, RedrawClientPacket):
      self.on_player_redraw()

  def on_player_riichi(self, player: GamePlayer):
    player.declare_riichi()
    self.update_player_states()

  def on_player_tsumo(self, player: GamePlayer, packet: TsumoClientPacket):
    self.distribute_riichi_points([player])

    player_points = tuple((
        player.points
        for player in self.game_state.players
    ))

    tsumo_wind = self.game_state.player_wind(player)
    dealer_tsumo = tsumo_wind == Wind.EAST
    for wind, other_player in self.game_state.players_by_wind:
      if other_player == player:
        continue

      is_dealer = wind == Wind.EAST
      points = score_calculator.tsumo(packet.han, packet.fu_index, dealer_tsumo or is_dealer)
      points += self.game_state.total_honba * TSUMO_HONBA_POINTS
      player.take_points(other_player, points)

    tsumo_hand = self.game_state.hand
    total_honba = self.game_state.total_honba

    if tsumo_wind == Wind.EAST:
      self.repeat_hand()
    else:
      self.next_hand()

    for index, p in enumerate(self.game_state.players):
      p.send_packet(TsumoServerPacket(
          game_state=ClientGameState(
              index,
              players=self.game_state.players,
              starting_points=self.game_state.starting_points,
              hand=self.game_state.hand,
              repeat=self.game_state.repeat,
              bonus_honba=self.game_state.bonus_honba,
              bonus_riichi=self.game_state.bonus_riichi,
          ),
          tsumo_wind=tsumo_wind,
          tsumo_hand=tsumo_hand,
          points=tuple((
              player.points - player_points[i]
              for i, player in enumerate(self.game_state.players)
          )),
      ))

  def on_player_ron(self, player: GamePlayer, packet: RonWindClientPacket):
    from .game_ron import GameRonPlayer, GameRonServerState

    if self.game_state.player_wind(player) == packet.from_wind:
      return

    players_by_wind = {
        player: wind
        for wind, player in self.game_state.players_by_wind
    }

    def ron_player(p: GamePlayer):
      if players_by_wind[p] == packet.from_wind:
        ron = 0
      else:
        ron = -1

      return GameRonPlayer(p.client, p.points, p.riichi, ron)

    self.child = GameRonServerState(
        self.server,
        GameState(
            players=tuple((
                ron_player(player)
                for player in self.game_state.players
            )),
            starting_points=self.game_state.starting_points,
            hand=self.game_state.hand,
            repeat=self.game_state.repeat,
            bonus_honba=self.game_state.bonus_honba,
            bonus_riichi=self.game_state.bonus_riichi,
        ),
        packet.from_wind,
    )

  def on_player_draw(self, player: GamePlayer, packet: DrawClientPacket):
    from .game_draw import GameDrawPlayer, GameDrawServerState

    def draw_player(p: GamePlayer):
      tenpai = packet.tenpai if p == player else Tenpai.UNKNOWN
      return GameDrawPlayer(p.client, p.points, p.riichi, tenpai)

    self.child = GameDrawServerState(
        self.server,
        GameState(
            players=tuple((
                draw_player(player)
                for player in self.game_state.players
            )),
            starting_points=self.game_state.starting_points,
            hand=self.game_state.hand,
            repeat=self.game_state.repeat,
            bonus_honba=self.game_state.bonus_honba,
            bonus_riichi=self.game_state.bonus_riichi,
        ),
    )

  def on_player_redraw(self):
    self.redraw()
    self.update_player_states()

  def update_player_states(self):
    for index, player in enumerate(self.game_state.players):
      player.send_packet(GameStateServerPacket(ClientGameState(
          index,
          players=self.game_state.players,
          starting_points=self.game_state.starting_points,
          hand=self.game_state.hand,
          repeat=self.game_state.repeat,
          bonus_honba=self.game_state.bonus_honba,
          bonus_riichi=self.game_state.bonus_riichi,
      )))
