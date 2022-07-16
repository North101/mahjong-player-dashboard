import select
import socket
from typing import Tuple

from mahjong.client import Client
from mahjong.packets import *
from mahjong.poll import Poll


Players = tuple[
    Type['GamePlayer'],
    Type['GamePlayer'],
    Type['GamePlayer'],
    Type['GamePlayer'],
]


DrawPlayers = tuple[
    Type['GameDrawPlayer'],
    Type['GameDrawPlayer'],
    Type['GameDrawPlayer'],
    Type['GameDrawPlayer'],
]


class Server:
  socket: Type['socket.socket']
  state: Type['ServerState']

  def __init__(self, poll: Poll, address: Tuple[str, int]):
    self.poll = poll
    self.address = address
    self.state = LobbyServerState(self)

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
  def state(self):
    return self.server.state

  @state.setter
  def state(self, state: Type['ServerState']):
    self.server.state = state

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


class LobbyServerState(ServerState):
  clients: Mapping[socket.socket, LobbyPlayer] = {}

  def __init__(self, server: Server):
    self.server = server

  def on_client_connect(self, client: socket.socket, address: Tuple[str, int]):
    self.clients[client] = LobbyPlayer(client)

    if len(self.clients) == len(Wind):
      self.state = GameServerState(self.server, self.clients.values())

  def on_client_disconnect(self, client: socket.socket):
    del self.clients[client]

  def on_client_packet(self, client: socket.socket, packet: Packet):
    pass


class GamePlayer:
  def __init__(self, client: socket.socket, points: int, riichi: bool = False):
    self.client = client
    self.points = points
    self.riichi = riichi

  def take_points(self, other: Type['GamePlayer'], points: int):
    self.points += points
    other.points -= points


class GameServerState(ServerState):
  def __init__(
      self, server: Server, players: List[LobbyPlayer],
      starting_points: int = 25000, hand: int = 0, repeat: int = 0, max_rounds: int = 1
  ):
    self.server = server

    self.hand = hand
    self.repeat = repeat
    self.max_rounds = max_rounds
    self.players = tuple(
        GamePlayer(player.client, starting_points)
        for player in players
    )
    self.update_player_states()

  def on_client_connect(self, client: socket.socket, address: Tuple[str, int]):
    pass

  def on_client_disconnect(self, client: socket.socket):
    pass

  def on_client_packet(self, client: socket.socket, packet: Packet):
    player = self.player_by_client(client)
    if type(packet) is RiichiClientPacket:
      self.on_player_riichi(player, packet)
    elif type(packet) is TsumoClientPacket:
      self.on_player_tsumo(player, packet)
    elif type(packet) is RonClientPacket:
      self.on_player_ron(player, packet)
    elif type(packet) is DrawClientPacket:
      self.on_player_draw(player, packet)

  def on_player_riichi(self, player: GamePlayer, packet: RiichiClientPacket):
    if not player.riichi:
      player.points -= 1000
      player.riichi = True
    self.update_player_states()

  def on_player_tsumo(self, player: GamePlayer, packet: TsumoClientPacket):
    self.declare_riichi()

    for other_player in self.players:
      if other_player == player:
        continue

      other_player_wind = self.player_wind(other_player)
      if other_player_wind == Wind.EAST:
        points = packet.dealer_points
      else:
        points = packet.points
      player.take_points(other_player, points)

    if self.player_wind(player) == Wind.EAST:
      self.repeat_hand()
    else:
      self.next_hand()

  def on_player_ron(self, player: GamePlayer, packet: RonClientPacket):
    self.declare_riichi()

    other_player = self.player_for_wind(packet.from_wind)
    player.take_points(other_player, packet.points)

    if self.player_wind(player) == Wind.EAST:
      self.repeat_hand()
    else:
      self.next_hand()

  def on_player_draw(self, player: GamePlayer, packet: DrawClientPacket):
    players = tuple((
        GameDrawPlayer(other_player.client, (
          packet.tenpai
          if player == other_player else
          None
        ))
        for other_player in self.players
    ))
    self.state = GameDrawServerState(self.server, self, players)

  def on_player_draw_complete(self, players: DrawPlayers):
    for draw_player in players:
      if not draw_player.tenpai:
        continue

      player = self.player_by_client(draw_player.client)
      for other_player in self.players:
        if player == other_player:
          continue

        player.take_points(other_player, 1000)

    east_index = self.player_index_for_wind(Wind.EAST)
    if players[east_index].tenpai:
      self.repeat_hand()
    else:
      self.next_hand()

  @property
  def round(self):
    return self.hand // 4

  def declare_riichi(self, player: GamePlayer):
    for player in self.players:
      if player.riichi:
        player.points += 1000

  def reset_riichi(self):
    for player in self.players:
      player.riichi = False

  def repeat_hand(self):
    self.reset_riichi()
    self.repeat += 1
    self.update_player_states()

  def next_hand(self):
    self.reset_riichi()
    self.hand += 1
    self.repeat = 0
    self.update_player_states()

  def player_by_client(self, client: socket.socket):
    return next((
        player
        for player in self.players
        if player.client == client
    ))

  def player_wind(self, player: GamePlayer):
    return list(Wind)[(self.players.index(player) + self.hand) % len(Wind)]

  def player_index_for_wind(self, wind: Wind):
    return (self.hand + wind) % len(Wind)

  def player_for_wind(self, wind: Wind):
    return self.players[self.player_index_for_wind(wind)]

  def update_player_states(self):
    for index, player in enumerate(self.players):
      send_msg(player.client, PlayerGameStateServerPacket(
          self.hand,
          self.repeat,
          index,
          self.players,
      ).pack())


class GameDrawPlayer:
  def __init__(self, client: socket.socket, tenpai: bool):
    self.client = client
    self.tenpai = tenpai


class GameDrawServerState(ServerState):
  def __init__(self, server: Server, game_state: GameServerState, players: DrawPlayers):
    self.server = server
    self.game_state = game_state

    self.players = players
    for player in players:
      if player.tenpai is not None: continue
      send_msg(player.client, DrawServerPacket().pack())

  def on_client_packet(self, client: socket.socket, packet: Packet):
    player = self.player_by_client(client)
    if type(packet) is DrawClientPacket:
      self.on_player_draw(player, packet)

  def on_player_draw(self, player: GameDrawPlayer, packet: DrawClientPacket):
    player.tenpai = packet.tenpai

    if all((player.tenpai is not None for player in self.players)):
      self.state = self.game_state
      self.state.on_player_draw_complete(self.players)

  def player_by_client(self, client: socket.socket):
    return next((
        player
        for player in self.players
        if player.client == client
    ))


def main():
  try:
    poll = Poll()
    server = Server(poll, ('127.0.0.1', 1246))
    server.start()
    client = Client(poll, ('127.0.0.1', 1246))
    client.start()
    while True:
      poll.poll()
  finally:
    lookup = list(poll.lookup.values())
    for event_callback in lookup:
      poll.unregister(event_callback.fd)


if __name__ == '__main__':
  main()
