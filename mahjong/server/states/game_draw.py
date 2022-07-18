import socket
from typing import TYPE_CHECKING, Callable, Optional, Tuple

from mahjong.packets import GameDrawClientPacket, GameDrawServerPacket, GameStateServerPacket, Packet
from mahjong.shared import GamePlayers, GameState

from .shared import ClientTuple, GamePlayer, ReconnectableGameStateMixin

if TYPE_CHECKING:
  from mahjong.server import Server


class GameDrawPlayer(GamePlayer):
  def __init__(self, client: socket.socket, points: int, riichi: bool, tenpai: Optional[bool]):
    self.client = client
    self.points = points
    self.riichi = riichi
    self.tenpai = tenpai


DrawPlayerTuple = Tuple[
    GameDrawPlayer,
    GameDrawPlayer,
    GameDrawPlayer,
    GameDrawPlayer,
]


class GameDrawServerState(ReconnectableGameStateMixin):
  def __init__(self, server: 'Server', game_state: GameState, players: DrawPlayerTuple,
               callback: Callable[[DrawPlayerTuple], None]):
    self.server = server
    self.game_state = game_state
    self.players: DrawPlayerTuple = players
    self.callback = callback

    for player in players:
      if player.tenpai is not None:
        continue
      player.send_packet(GameDrawServerPacket())
  
  def on_game_reconnect(self, clients: ClientTuple):
    super().on_game_reconnect(clients)

    for index, player in enumerate(self.players):
      player.send_packet(GameStateServerPacket(self.game_state, index, self.players))
      if player.tenpai is not None:
        continue
      player.send_packet(GameDrawServerPacket())

  def on_client_packet(self, client: socket.socket, packet: Packet):
    player = self.player_for_client(client)
    if not player:
      return
    elif isinstance(packet, GameDrawClientPacket):
      self.on_player_draw(player, packet)

  def on_player_draw(self, player: GameDrawPlayer, packet: GameDrawClientPacket):
    player.tenpai = packet.tenpai

    if all((player.tenpai is not None for player in self.players)):
      self.callback(self.players)
