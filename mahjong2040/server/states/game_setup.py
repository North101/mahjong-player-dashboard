import typing

from mahjong2040.packets import (
    ConfirmWindServerPacket,
    Packet,
    SetupPlayerCountErrorServerPacket,
    SetupPlayerWindClientPacket,
    SetupPlayerWindServerPacket,
)
from mahjong2040.shared import STARTING_POINTS, GamePlayerMixin, GameState, Wind

from .base import ServerState
from .game import GameServerState
from .shared import GamePlayer, ServerClient

if typing.TYPE_CHECKING:
  from mahjong2040.server import Server


class GameSetupServerState(ServerState):
  def __init__(self, server: Server, game_state: GameState[GamePlayerMixin] | None = None):
    super().__init__(server)

    self.players: list[ServerClient] = []
    self.game_state = game_state

  def init(self):
    self.ask_next_wind()

  def ask_next_wind(self):
    wind = len(self.players)
    packet = SetupPlayerWindServerPacket(wind)
    for client in self.clients:
      client.send_packet(packet)

  def on_client_leave(self, client: ServerClient):
    super().on_client_leave(client)
    if client in self.clients:
      if not self.enough_players():
        return self.to_lobby()
    elif client in self.players:
      player_index = self.players.index(client)
      self.players.remove(client)
      if not self.enough_players():
        return self.to_lobby()

      if player_index < len(self.players):
        self.players = []

      self.ask_next_wind()

  def on_client_packet(self, client: ServerClient, packet: Packet):
    if isinstance(packet, SetupPlayerWindClientPacket):
      if packet.wind != len(self.players) and client not in self.players:
        return

      self.players.append(client)
      client.send_packet(ConfirmWindServerPacket(packet.wind))

      if len(self.players) == len(Wind):
        game_state = self.game_state
        self.child = GameServerState(
            server=self.server,
            game_state=GameState(
              players=tuple((
                  GamePlayer(
                    player,
                    game_state.players[i].points if game_state else STARTING_POINTS,
                    game_state.players[i].riichi if game_state else False,
                  )
                  for i, player in enumerate(self.players)
              )),
              starting_points=game_state.starting_points if game_state else STARTING_POINTS,
              hand=game_state.hand if game_state else 0,
              repeat=game_state.starting_points if game_state else 0,
              bonus_honba=game_state.bonus_honba if game_state else 0,
              bonus_riichi=game_state.bonus_riichi if game_state else 0,
          ),
        )
      else:
        self.ask_next_wind()

  def enough_players(self):
    return len(self.clients) >= len(Wind)

  def to_lobby(self):
    from .lobby import LobbyServerState

    packet = SetupPlayerCountErrorServerPacket()
    for client in self.clients:
      client.send_packet(packet)
    self.child = LobbyServerState(self.server)
