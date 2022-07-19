import socket
from typing import TYPE_CHECKING, Callable, TypeVar

from mahjong.packets import (GameReconnectStatusServerPacket,
                             GameStateServerPacket, Packet,
                             SetupConfirmWindServerPacket,
                             SetupSelectWindClientPacket,
                             SetupSelectWindServerPacket, send_msg,
                             send_packet)
from mahjong.shared import Address, GamePlayerTuple, GameState, GameStateMixin
from mahjong.wind import Wind

from .base import ServerState
from .shared import ClientList, GamePlayer

if TYPE_CHECKING:
  from mahjong.server import Server


T = TypeVar('T', bound=GamePlayer)


class GameReconnectServerState(ServerState, GameStateMixin[T]):
  def __init__(self, server: 'Server', game_state: GameState,
               players: GamePlayerTuple[T], callback: Callable[[ClientList], None]):
    self.server = server
    self.game_state = game_state
    self.players = players

    player1, player2, player3, player4 = players
    self.player_clients = [
        player1.client,
        player2.client,
        player3.client,
        player4.client,
    ]
    self.callback = callback

    self.ask_wind()

  def on_client_connect(self, client: socket.socket, address: Address):
    super().on_client_connect(client, address)

    self.send_client_select_wind_packet(client, self.wind)

  def on_client_disconnect(self, client: socket.socket):
    super().on_client_disconnect(client)

    if client not in self.player_clients:
      return

    self.ask_wind()

  def on_client_packet(self, client: socket.socket, packet: Packet):
    if isinstance(packet, SetupSelectWindClientPacket):
      if self.wind == packet.wind:
        self.player_clients[self.player_index_for_wind(self.wind)] = client
        send_packet(client, SetupConfirmWindServerPacket(packet.wind))
        index = self.player_index_for_wind(self.wind)
        send_packet(client, GameStateServerPacket(self.game_state, index, self.players))

      self.ask_wind()

  def missing_winds(self):
    for wind in Wind:
      player_client = self.player_clients[self.player_index_for_wind(wind)]
      if player_client not in self.clients:
        yield wind

  def ask_wind(self):
    try:
      self.wind = next(self.missing_winds())
    except StopIteration:
      self.callback(self.player_clients)
      return

    for client in self.clients:
      if client in self.player_clients:
        self.send_client_reconnect_status_packet(client, set(self.missing_winds()))
      else:
        self.send_client_select_wind_packet(client, self.wind)

  def send_client_reconnect_status_packet(self, client: socket.socket, missing_winds: set[Wind]):
    send_msg(client, GameReconnectStatusServerPacket(missing_winds).pack())

  def send_client_select_wind_packet(self, client: socket.socket, wind: Wind):
    send_msg(client, SetupSelectWindServerPacket(wind).pack())
