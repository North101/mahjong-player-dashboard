import socket

from mahjong2040.packets import (
    ConfirmWindServerPacket,
    GameReconnectStatusServerPacket,
    GameStateServerPacket,
    Packet,
    SelectWindClientPacket,
    SelectWindServerPacket,
    send_packet,
)
from mahjong2040.shared import Address, ClientGameState, GameState, Wind

from .base import ServerState
from .shared import GamePlayerType


class GameReconnectServerState(ServerState):
  def __init__(self, server, game_state: GameState[GamePlayerType], callback):
    self.server = server
    self.game_state = game_state

    player1, player2, player3, player4 = game_state.players
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
    if isinstance(packet, SelectWindClientPacket):
      if self.wind == packet.wind:
        self.player_clients[self.game_state.player_index_for_wind(self.wind)] = client
        send_packet(client, ConfirmWindServerPacket(packet.wind))

        index = self.game_state.player_index_for_wind(self.wind)
        send_packet(client, GameStateServerPacket(ClientGameState(
            index,
            self.game_state.players,
            self.game_state.hand,
            self.game_state.repeat,
            self.game_state.bonus_honba,
            self.game_state.bonus_riichi,
        )))

      self.ask_wind()

  def missing_winds(self):
    for wind in range(len(Wind)):
      player_client = self.player_clients[self.game_state.player_index_for_wind(wind)]
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

  def send_client_reconnect_status_packet(self, client: socket.socket, missing_winds: set[int]):
    send_packet(client, GameReconnectStatusServerPacket(missing_winds))

  def send_client_select_wind_packet(self, client: socket.socket, wind: int):
    send_packet(client, SelectWindServerPacket(wind))
