import select
import socket
from typing import Tuple

from mahjong.client import Client
from mahjong.packets import *
from mahjong.poll import Poll


class Server:
  socket: Type['socket.socket']
  state: Type['ServerState']

  def __init__(self, poll: Poll, address: Tuple[str, int]):
    self.poll = poll
    self.address = address
    self.state = ServerLobbyState(self)

  def start(self):
    host, port = self.address

    self.socket = socket.socket()
    self.socket.bind((host, port))

    print(f'Server is listing on the port {port}...')
    self.socket.listen()

    self.poll.register(self.socket, select.POLLIN, self.on_server_data)

  def on_server_data(self, fd: socket.socket, event: int):
    self.state.on_server_data(fd, event)

  def on_client_data(self, fd: socket.socket, event: int):
    self.state.on_client_data(fd, event)


class ServerState:
  def __init__(self, server: Server):
    self.server = server

  @property
  def poll(self):
    return self.server.poll

  def on_server_data(self, server: socket.socket, event: int):
    if event & select.POLLIN:
      client, address = server.accept()
      self.on_client_connect(client, address)
      self.poll.register(client, select.POLLIN, self.server.on_client_data)

  def on_client_data(self, client: socket.socket, event: int):
    if event & select.POLLHUP:
      self.poll.unregister(client)
      self.on_client_disconnect(client)
    elif event & select.POLLIN:
      self.on_client_packet(client, read_packet(client))

  def on_client_connect(self, client: socket.socket, address: Tuple[str, int]):
    raise NotImplementedError()

  def on_client_disconnect(self, client: socket.socket):
    raise NotImplementedError()

  def on_client_packet(self, client: socket.socket, packet: Packet):
    raise NotImplementedError()


class LobbyPlayer:
  def __init__(self, client: socket.socket):
    self.client = client


class ServerLobbyState(ServerState):
  clients: Mapping[socket.socket, LobbyPlayer] = {}

  def __init__(self, server: Server):
    self.server = server

  def on_client_connect(self, client: socket.socket, address: Tuple[str, int]):
    self.clients[client] = LobbyPlayer(client)

    if len(self.clients) == len(Wind):
      self.server.state = ServerGameState(self.server, self.clients.values())

  def on_client_disconnect(self, client: socket.socket):
    del self.clients[client]

  def on_client_packet(self, client: socket.socket, packet: Packet):
    pass


class GamePlayer:
  def __init__(self, client: socket.socket, points: int, riichi: bool = False):
    self.client = client
    self.points = points
    self.riichi = riichi


class ServerGameState(ServerState):
  players: List[GamePlayer] = []

  def __init__(
      self, server: Server, players: List[LobbyPlayer],
      starting_points: int = 25000, hand: int = 0, repeat: int = 0, max_rounds: int = 1
  ):
    self.server = server

    self.hand = hand
    self.repeat = repeat
    self.max_rounds = max_rounds
    self.players = [
        GamePlayer(player.client, starting_points)
        for player in players
    ]
    self.update_player_states()

  def on_client_connect(self, client: socket.socket, address: Tuple[str, int]):
    pass

  def on_client_disconnect(self, client: socket.socket):
    pass

  def on_client_packet(self, client: socket.socket, packet: Packet):
    player = self.player_by_client(client)
    if type(packet) is RiichiPacket:
      self.on_player_riichi(player, packet)
    elif type(packet) is TsumoPacket:
      self.on_player_tsumo(player, packet)
    elif type(packet) is RonPacket:
      self.on_player_ron(player, packet)
    elif type(packet) is DrawPacket:
      self.on_player_draw(player, packet)

  def on_player_riichi(self, player: GamePlayer, packet: RiichiPacket):
    if not player.riichi:
      player.points -= 1000
      player.riichi = True
    self.update_player_states()

  def on_player_tsumo(self, player: GamePlayer, packet: TsumoPacket):
    self.take_riichi()

    for other_player in self.players:
      if other_player == player:
        continue

      other_player_wind = self.player_wind(other_player)
      if other_player_wind == Wind.EAST:
        points = packet.dealer_points
      else:
        points = packet.points
      player.points += points
      other_player.points -= points

    if self.player_wind(player) == Wind.EAST:
      self.repeat_hand()
    else:
      self.next_hand()

  def on_player_ron(self, player: GamePlayer, packet: RonPacket):
    self.take_riichi()

    other_player = self.player_for_wind(packet.from_wind)
    player.points += packet.points
    other_player.points -= packet.points

    if self.player_wind(player) == Wind.EAST:
      self.repeat_hand()
    else:
      self.next_hand()

  def on_player_draw(self, player: GamePlayer, packet: DrawPacket):
    self.next_hand()

  @property
  def round(self):
    return self.hand % 4
  
  def take_riichi(self, player: GamePlayer):
    for other_player in self.players:
      if other_player.riichi:
        player.points += 1000
  
  def reset_riichi(self):
    for other_player in self.players:
      other_player.riichi = False

  def repeat_hand(self):
    self.repeat += 1
    self.reset_riichi()
    self.update_player_states()

  def next_hand(self):
    self.hand += 1
    self.repeat = 0
    self.reset_riichi()
    self.update_player_states()

  def player_by_client(self, client: socket.socket):
    return next((
        player
        for player in self.players
        if player.client == client
    ), None)

  def player_wind(self, player: GamePlayer):
    return list(Wind)[(self.players.index(player) + self.hand) % len(Wind)]

  def player_for_wind(self, wind: Wind):
    return self.players[(self.hand + wind) % len(Wind)]

  def update_player_states(self):
    for index, player in enumerate(self.players):
      send_msg(player.client, PlayerGameStatePacket(
          self.hand,
          self.repeat,
          index,
          self.players,
      ).pack())


def main():
  poll = Poll()
  server = Server(poll, ('127.0.0.1', 1246))
  server.start()
  client = Client(poll, ('127.0.0.1', 1246))
  client.start()
  while True:
    poll.poll()


if __name__ == '__main__':
  main()
