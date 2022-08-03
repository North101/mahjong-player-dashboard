import socket

from mahjong2040.packets import (DrawClientPacket,
                                       DrawServerPacket,
                                       GameStateServerPacket, Packet)
from mahjong2040.shared import (DRAW_POINTS, ClientGameState,
                                      GamePlayerTuple, GameState, TenpaiState)

from .shared import BaseGameServerStateMixin, GamePlayer


class GameDrawPlayer(GamePlayer):
  def __init__(self, client: socket.socket, points: int, riichi: bool, tenpai: int):
    self.client = client
    self.points = points
    self.riichi = riichi
    self.tenpai = tenpai


class GameDrawServerState(BaseGameServerStateMixin):
  def __init__(self, server, game_state: GameState, players: GamePlayerTuple):
    self.server = server
    self.game_state = game_state
    self.players = players

    for player in players:
      if player.tenpai is not None:
        continue
      player.send_packet(DrawServerPacket())

  def on_players_reconnect(self, clients: list[socket.socket]):
    super().on_players_reconnect(clients)

    for index, player in enumerate(self.players):
      player.send_packet(GameStateServerPacket(ClientGameState(
          index,
          self.players,
          self.game_state.hand,
          self.game_state.repeat,
          self.game_state.bonus_honba,
          self.game_state.bonus_riichi,
      )))
      if player.tenpai is not None:
        continue
      player.send_packet(DrawServerPacket())

  def on_client_packet(self, client: socket.socket, packet: Packet):
    player = self.player_for_client(client)
    if not player:
      return
    elif isinstance(packet, DrawClientPacket):
      self.on_player_draw(player, packet)

  def on_player_draw(self, player: GameDrawPlayer, packet: DrawClientPacket):
    player.tenpai = packet.tenpai

    self.on_player_draw_complete()

  def on_player_draw_complete(self):
    from mahjong2040.server.states.game import GameServerState

    if any((player.tenpai == TenpaiState.unknown for player in self.players)):
      return

    winners = [
        player
        for player in self.players
        if player.tenpai == True
    ]
    for player in winners:
      for other_player in self.players:
        if player == other_player:
          continue
        player.take_points(other_player, DRAW_POINTS)

    if self.player_for_wind(0) in winners:
      self.repeat_hand(draw=True)
    else:
      self.next_hand(draw=True)

    self.child = GameServerState(self.server, self.game_state, self.players)
