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
from mahjong2040.shared import (
    TSUMO_HONBA_POINTS,
    ClientGameState,
    GamePlayerTuple,
    GameState,
    Tenpai,
    Wind,
)

from .shared import BaseGameServerStateMixin, GamePlayerType, ServerClient


class GameServerState(BaseGameServerStateMixin):
  def __init__(self, server, game_state: GameState[GamePlayerType]):
    self.server = server
    self.game_state = game_state

  def init(self):
    self.update_player_states()

  def on_players_reconnect(self, players):
    super().on_players_reconnect(players)

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

  def on_player_riichi(self, player: GamePlayerType):
    player.declare_riichi()
    self.update_player_states()

  def on_player_tsumo(self, player: GamePlayerType, packet: TsumoClientPacket):
    self.take_riichi_points([player])

    from_dealer = self.game_state.player_wind(player) == Wind.EAST
    for other_player in self.game_state.players:
      if other_player == player:
        continue

      if from_dealer:
        points = packet.dealer_points
      else:
        points = packet.points
      points += self.game_state.total_honba * TSUMO_HONBA_POINTS
      player.take_points(other_player, points)

    tsumo_wind = self.game_state.player_wind(player)
    tsumo_hand = self.game_state.hand
    total_honba = self.game_state.total_honba

    if self.game_state.player_wind(player) == 0:
      self.repeat_hand()
    else:
      self.next_hand()

    for index, p in enumerate(self.game_state.players):
      p.send_packet(TsumoServerPacket(
        game_state=ClientGameState(
          index,
          players=self.game_state.players,
          hand=self.game_state.hand,
          repeat=self.game_state.repeat,
          bonus_honba=self.game_state.bonus_honba,
          bonus_riichi=self.game_state.bonus_riichi,
        ),
        tsumo_wind=tsumo_wind,
        tsumo_hand=tsumo_hand,
        dealer_points=packet.dealer_points + (total_honba * TSUMO_HONBA_POINTS),
        nondealer_points=packet.points + (total_honba * TSUMO_HONBA_POINTS),
      ))

  def on_player_ron(self, player: GamePlayerType, packet: RonWindClientPacket):
    from .game_ron import GameRonPlayer, GameRonServerState

    if self.game_state.player_wind(player) == packet.from_wind:
      return

    players_by_wind = {
        player: wind
        for wind, player in self.game_state.players_by_wind
    }

    def ron_player(p: GamePlayerType):
      if players_by_wind[p] == packet.from_wind:
        ron = 0
      else:
        ron = -1

      return GameRonPlayer(p.client, p.points, p.riichi, ron)

    player1, player2, player3, player4 = self.game_state.players
    self.child = GameRonServerState(
        self.server,
        GameState(
            players=GamePlayerTuple(
                ron_player(player1),
                ron_player(player2),
                ron_player(player3),
                ron_player(player4),
            ),
            hand=self.game_state.hand,
            repeat=self.game_state.repeat,
            bonus_honba=self.game_state.bonus_honba,
            bonus_riichi=self.game_state.bonus_riichi,
        ),
        packet.from_wind,
    )

  def on_player_draw(self, player: GamePlayerType, packet: DrawClientPacket):
    from .game_draw import GameDrawPlayer, GameDrawServerState

    def draw_player(p: GamePlayerType):
      tenpai = packet.tenpai if p == player else Tenpai.UNKNOWN
      return GameDrawPlayer(p.client, p.points, p.riichi, tenpai)

    player1, player2, player3, player4 = self.game_state.players
    self.child = GameDrawServerState(
        self.server,
        GameState(
            players=GamePlayerTuple(
                draw_player(player1),
                draw_player(player2),
                draw_player(player3),
                draw_player(player4),
            ),
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
          hand=self.game_state.hand,
          repeat=self.game_state.repeat,
          bonus_honba=self.game_state.bonus_honba,
          bonus_riichi=self.game_state.bonus_riichi,
      )))
