from mahjong2040.packets import (
    ConfirmWindServerPacket,
    GameReconnectStatusServerPacket,
    GameStateServerPacket,
    Packet,
    SetupPlayerWindClientPacket,
    SetupPlayerWindServerPacket,
)
from mahjong2040.shared import ClientGameState, GameState, Wind

from .base import ServerState
from .shared import GamePlayerType, ServerClient


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

  def on_client_join(self, client: ServerClient):
    client.send_packet(SetupPlayerWindServerPacket(self.wind))

  def on_client_leave(self, client: ServerClient):
    if client not in self.player_clients:
      return

    self.ask_wind()

  def on_client_packet(self, client: ServerClient, packet: Packet):
    if isinstance(packet, SetupPlayerWindClientPacket):
      if self.wind == packet.wind:
        self.player_clients[self.game_state.player_index_for_wind(self.wind)] = client
        client.send_packet(ConfirmWindServerPacket(packet.wind))

        index = self.game_state.player_index_for_wind(self.wind)
        client.send_packet(GameStateServerPacket(ClientGameState(
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
        client.send_packet(GameReconnectStatusServerPacket(set(self.missing_winds())))
      else:
        client.send_packet(SetupPlayerWindServerPacket(self.wind))
