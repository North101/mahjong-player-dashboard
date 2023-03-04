from mahjong2040.packets import (
    ConfirmWindServerPacket,
    Packet,
    SetupPlayerCountErrorServerPacket,
    SetupPlayerWindClientPacket,
    SetupPlayerWindServerPacket,
)
from mahjong2040.shared import STARTING_POINTS, GamePlayerTuple, GameState, Wind

from .base import ServerState
from .game import GameServerState
from .shared import GamePlayer, ServerClient


class GameSetupServerState(ServerState):
  def __init__(self, server):
    super().__init__(server)

    self.players: list[ServerClient] = []
    self.ask_next_wind()

  def ask_next_wind(self):
    wind = len(self.players)
    packet = SetupPlayerWindServerPacket(wind)
    for client in self.clients:
      if client not in self.players:
        client.send_packet(packet)

  def on_client_leave(self, client: ServerClient):
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
        self.child = GameServerState(
            server=self.server,
            game_state=GameState(
                players=GamePlayerTuple(
                    GamePlayer(self.players[0], STARTING_POINTS),
                    GamePlayer(self.players[1], STARTING_POINTS),
                    GamePlayer(self.players[2], STARTING_POINTS),
                    GamePlayer(self.players[3], STARTING_POINTS),
                ),
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
      client.send_packet(client)
    self.child = LobbyServerState(self.server)
