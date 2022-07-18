import socket

from mahjong.packets import *
from mahjong.poll import *
from mahjong.shared import *

from .base import *
from .game import *

if TYPE_CHECKING:
  from mahjong.server import Server


class GameSetupServerState(ServerState):
  def __init__(self, server: 'Server'):
    super().__init__(server)

    self.players: List[socket.socket] = []
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
        self.state = GameServerState(self.server, (
            self.players[0],
            self.players[1],
            self.players[2],
            self.players[3],
        ))
      else:
        self.ask_next_wind()

  def enough_players(self):
    return len(self.clients) >= len(Wind)

  def to_lobby(self):
    from mahjong.server.states.lobby import LobbyServerState

    packet = SetupNotEnoughServerPacket().pack()
    for client in self.clients:
      send_msg(client, packet)
    self.state = LobbyServerState(self.server)
