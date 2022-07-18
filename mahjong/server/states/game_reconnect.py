from mahjong.packets import *
from mahjong.poll import *
from mahjong.shared import *

from .base import *

if TYPE_CHECKING:
  from .game import GameServerState


class ReconnectPlayer(ClientMixin):
  def __init__(self, client: socket.socket, points: int, riichi: bool):
    self.client = client
    self.points = points
    self.riichi = riichi


ReconnectPlayers = Tuple[
    ReconnectPlayer,
    ReconnectPlayer,
    ReconnectPlayer,
    ReconnectPlayer,
]


class GameReconnectServerState(ServerState):
  def __init__(self, game_state: 'GameServerState', callback: Callable[[ReconnectPlayers], None]):
    self.game_state = game_state

    player1, player2, player3, player4 = game_state.players
    self.players = (
        ReconnectPlayer(player1.client, player1.points, player1.riichi),
        ReconnectPlayer(player2.client, player2.points, player2.riichi),
        ReconnectPlayer(player3.client, player4.points, player3.riichi),
        ReconnectPlayer(player4.client, player4.points, player4.riichi),
    )
    self.callback = callback

    self.ask_wind()

  @property
  def server(self):
    return self.game_state.server
  
  @property
  def hand(self):
    return self.game_state.hand

  def on_client_connect(self, client: socket.socket, address: Tuple[str, int]):
    super().on_client_connect(client, address)

    self.send_client_wind_packet(client, self.wind)

  def on_client_disconnect(self, client: socket.socket):
    super().on_client_disconnect(client)

    player = self.player_for_client(client)
    if not player:
      return

    self.ask_wind()

  def on_client_packet(self, client: socket.socket, packet: Packet):
    if isinstance(packet, SetupSelectWindClientPacket):
      player = self.player_for_client(client)
      if player:
        return

      elif self.wind == packet.wind:
        player = self.players[(self.wind + self.hand) % len(Wind)]
        player.client = client
        player.send_packet(SetupConfirmWindServerPacket(packet.wind))
      
      self.ask_wind()

  def player_for_client(self, client: socket.socket):
    try:
      return next((
          player
          for player in self.players
          if player.client == client
      ))
    except StopIteration:
      return None

  def missing_winds(self):
    for wind in Wind:
      player = self.players[(wind + self.hand) % len(Wind)]
      if player.client not in self.clients:
        yield wind

  def ask_wind(self):
    from mahjong.server.states.game import GamePlayer

    try:
      self.wind = next(self.missing_winds())
    except StopIteration:
      player1, player2, player3, player4 = self.players
      self.callback((
        GamePlayer(player1.client, player1.points, player1.riichi),
        GamePlayer(player2.client, player2.points, player2.riichi),
        GamePlayer(player3.client, player3.points, player3.riichi),
        GamePlayer(player4.client, player4.points, player4.riichi),
      ))
      return

    player_clients = [
        player.client
        for player in self.players
    ]
    for client in self.clients:
      if client in player_clients:
        continue
      self.send_client_wind_packet(client, self.wind)

  def send_client_wind_packet(self, client: socket.socket, wind: Wind):
    send_msg(client, SetupSelectWindServerPacket(wind).pack())
