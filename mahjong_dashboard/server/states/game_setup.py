import socket
from typing import TYPE_CHECKING

from mahjong_dashboard.packets import (Packet, SetupConfirmWindServerPacket,
                             SetupNotEnoughServerPacket,
                             SetupSelectWindClientPacket,
                             SetupSelectWindServerPacket, send_msg)
from mahjong_dashboard.shared import GamePlayerTuple, GameState
from mahjong_dashboard.wind import Wind

from .base import ServerState
from .game import GameServerState
from .shared import ClientList, GamePlayer

if TYPE_CHECKING:
  from mahjong_dashboard.server import Server


class GameSetupServerState(ServerState):
  def __init__(self, server: 'Server'):
    super().__init__(server)

    self.players = ClientList()
    self.ask_next_wind()

  def ask_next_wind(self):
    wind = Wind(len(self.players))
    packet = SetupSelectWindServerPacket(wind).pack()
    for client in self.clients:
      if client not in self.players:
        send_msg(client, packet)

  def on_client_disconnect(self, client: socket.socket):
    super().on_client_disconnect(client)

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

  def on_client_packet(self, client: socket.socket, packet: Packet):
    if isinstance(packet, SetupSelectWindClientPacket):
      if packet.wind != len(self.players) and client not in self.players:
        return

      self.players.append(client)
      send_msg(client, SetupConfirmWindServerPacket(packet.wind).pack())

      if len(self.players) == len(Wind):
        self.state = GameServerState(
            server=self.server,
            game_state=GameState(),
            players=GamePlayerTuple(
                GamePlayer(self.players[0], 25000),
                GamePlayer(self.players[1], 25000),
                GamePlayer(self.players[2], 25000),
                GamePlayer(self.players[3], 25000),
            ),
        )
      else:
        self.ask_next_wind()

  def enough_players(self):
    return len(self.clients) >= len(Wind)

  def to_lobby(self):
    from .lobby import LobbyServerState

    packet = SetupNotEnoughServerPacket().pack()
    for client in self.clients:
      send_msg(client, packet)
    self.state = LobbyServerState(self.server)
