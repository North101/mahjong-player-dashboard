import io
import socket
import struct

from mahjong_dashboard.shared import (GamePlayerMixin, GamePlayerTuple,
                                      GameState)
from mahjong_dashboard.wind import Wind


class Struct:
  fmt: str

  def pack(self) -> bytes:
    raise NotImplementedError()

  @classmethod
  def unpack(self, data: bytes):
    raise NotImplementedError()

  @classmethod
  def size(self):
    return struct.calcsize(self.fmt)


class Packet(Struct):
  id: int


class GameRiichiClientPacket(Packet):
  fmt = 'B'
  id = 2

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id)

  @classmethod
  def unpack(self, data: bytes):
    id, = struct.unpack(self.fmt, data)
    if id != self.id:
      raise ValueError(id)
    return GameRiichiClientPacket()

  def __repr__(self) -> str:
    return f'[{self.id}]: {self.__class__.__name__}()'


class GameTsumoClientPacket(Packet):
  fmt = 'BHH'
  id = 3

  def __init__(self, dealer_points, points):
    self.dealer_points = dealer_points
    self.points = points

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id, self.dealer_points, self.points)

  @classmethod
  def unpack(self, data: bytes):
    id, dealer_points, points = struct.unpack(self.fmt, data)
    if id != self.id:
      raise ValueError(id)
    return GameTsumoClientPacket(dealer_points, points)

  def __repr__(self) -> str:
    return f'[{self.id}]: {self.__class__.__name__}({self.dealer_points}, {self.points})'


class GameRonClientPacket(Packet):
  fmt = 'BBH'
  id = 4

  def __init__(self, from_wind: int, points: int):
    self.from_wind = from_wind
    self.points = points

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id, self.from_wind, self.points)

  @classmethod
  def unpack(self, data: bytes):
    id, from_wind, points = struct.unpack(self.fmt, data)
    if id != self.id:
      raise ValueError(id)
    return GameRonClientPacket(from_wind, points)

  def __repr__(self) -> str:
    return f'[{self.id}]: {self.__class__.__name__}({self.from_wind, self.points})'


class GameDrawClientPacket(Packet):
  fmt = 'BB'
  id = 5

  def __init__(self, tenpai: int):
    self.tenpai = tenpai

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id, self.tenpai)

  @classmethod
  def unpack(self, data: bytes):
    id, tenpai = struct.unpack(self.fmt, data)
    if id != self.id:
      raise ValueError(id)
    return GameDrawClientPacket(tenpai)

  def __repr__(self) -> str:
    return f'[{self.id}]: {self.__class__.__name__}({self.tenpai})'


class SetupSelectWindClientPacket(Packet):
  fmt = 'BB'
  id = 6

  def __init__(self, wind: int):
    self.wind = wind

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id, self.wind)

  @classmethod
  def unpack(self, data: bytes):
    id, wind = struct.unpack(self.fmt, data)

    if id != self.id:
      raise ValueError(id)
    return SetupSelectWindClientPacket(wind)


class PlayerStruct(Struct, GamePlayerMixin):
  fmt = 'HB'

  def __init__(self, points: int, riichi: bool) -> None:
    self.points = points
    self.riichi = riichi

  def pack(self):
    return struct.pack(self.fmt, self.points, 1 if self.riichi else 0)

  @classmethod
  def unpack(self, data: bytes, offset=0):
    points, riichi = struct.unpack_from(self.fmt, data, offset)
    return PlayerStruct(points, riichi != 0)

  def __repr__(self) -> str:
    return f'{self.__class__.__name__}({self.points}, {self.riichi})'


class GameStateServerPacket(Packet):
  fmt = 'BHHHHB'
  id = 7

  def __init__(self, game_state: GameState, player_index: int, players: GamePlayerTuple):
    self.game_state = game_state
    self.player_index = player_index
    self.players = players

  def pack(self) -> bytes:
    data = struct.pack(self.fmt, 
        self.id,
        self.game_state.hand,
        self.game_state.repeat,
        self.game_state.bonus_honba,
        self.game_state.bonus_riichi,
        self.player_index,
    )
    for player in self.players:
      data += PlayerStruct(player.points, player.riichi).pack()
    return data

  @classmethod
  def unpack(self, data: bytes, offset=0):
    id, hand, repeat, bonus_honba, bonus_riichi, player_index = struct.unpack_from(self.fmt, 
        data, offset)
    game_state = GameState(hand, repeat, bonus_honba, bonus_riichi)

    size = struct.calcsize(self.fmt)
    player_size = PlayerStruct.size()
    players = GamePlayerTuple(
        PlayerStruct.unpack(data, size + (player_size * 0)),
        PlayerStruct.unpack(data, size + (player_size * 1)),
        PlayerStruct.unpack(data, size + (player_size * 2)),
        PlayerStruct.unpack(data, size + (player_size * 3)),
    )

    if id != self.id:
      raise ValueError(id)
    return GameStateServerPacket(game_state, player_index, players)

  @classmethod
  def size(self):
    return self.fmt.size + (PlayerStruct.size() * len(Wind))

  def __repr__(self) -> str:
    return f'[{self.id}]: {self.__class__.__name__}({self.game_state}, {self.player_index}, {self.players})'


class GameDrawServerPacket(Packet):
  fmt = 'B'
  id = 8

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id)

  @classmethod
  def unpack(self, data: bytes):
    id, = struct.unpack(self.fmt, data)

    if id != self.id:
      raise ValueError(id)
    return GameDrawServerPacket()


class GameRonServerPacket(Packet):
  fmt = 'BB'
  id = 9

  def __init__(self, from_wind: int):
    self.from_wind = from_wind

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id, self.from_wind)

  @classmethod
  def unpack(self, data: bytes):
    id, from_wind = struct.unpack(self.fmt, data)

    if id != self.id:
      raise ValueError(id)
    return GameRonServerPacket(from_wind)


class SetupSelectWindServerPacket(Packet):
  fmt = 'BB'
  id = 10

  def __init__(self, wind: int):
    self.wind = wind

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id, self.wind)

  @classmethod
  def unpack(self, data: bytes):
    id, wind = struct.unpack(self.fmt, data)

    if id != self.id:
      raise ValueError(id)
    return SetupSelectWindServerPacket(wind)


class SetupConfirmWindServerPacket(Packet):
  fmt = 'BB'
  id = 11

  def __init__(self, wind: int):
    self.wind = wind

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id, self.wind)

  @classmethod
  def unpack(self, data: bytes):
    id, wind = struct.unpack(self.fmt, data)

    if id != self.id:
      raise ValueError(id)
    return SetupConfirmWindServerPacket(wind)


class SetupNotEnoughServerPacket(Packet):
  fmt = 'B'
  id = 12

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id)

  @classmethod
  def unpack(self, data: bytes):
    id, = struct.unpack(self.fmt, data)

    if id != self.id:
      raise ValueError(id)
    return SetupNotEnoughServerPacket()


class LobbyPlayersServerPacket(Packet):
  fmt = 'BHH'
  id = 13

  def __init__(self, count: int, max_players: int):
    self.count = count
    self.max_players = max_players

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id, self.count, self.max_players)

  @classmethod
  def unpack(self, data: bytes):
    id, count, max_players = struct.unpack(self.fmt, data)

    if id != self.id:
      raise ValueError(id)
    return LobbyPlayersServerPacket(count, max_players)


class GameReconnectStatusServerPacket(Packet):
  fmt = 'BB'
  id = 14

  def __init__(self, missing_winds: set[int]):
    self.missing_winds = missing_winds

  def pack(self) -> bytes:
    value = 0
    for wind in self.missing_winds:
      value |= (1 << wind)
    return struct.pack(self.fmt, self.id, value)

  @classmethod
  def unpack(self, data: bytes):
    id, missing_winds = struct.unpack(self.fmt, data)

    if id != self.id:
      raise ValueError(id)
    return GameReconnectStatusServerPacket({
        wind
        for wind in range(len(Wind))
        if (missing_winds >> wind & 1) != 0
    })


packets = [
    SetupSelectWindClientPacket,
    GameRiichiClientPacket,
    GameTsumoClientPacket,
    GameRonClientPacket,
    GameDrawClientPacket,

    LobbyPlayersServerPacket,
    SetupSelectWindServerPacket,
    SetupConfirmWindServerPacket,
    SetupNotEnoughServerPacket,
    GameStateServerPacket,
    GameDrawServerPacket,
    GameRonServerPacket,
    GameReconnectStatusServerPacket,
]


def find_packet(id):
  for packet in packets:
    if packet.id == id:
      return packet

  raise ValueError(id)


def unpack_id(data) -> int:
  return struct.unpack_from('B', data)[0]


def unpack_packet(data) -> Packet:
  id = unpack_id(data)
  return find_packet(id).unpack(data)


def read_packet(_socket: socket.socket):
  try:
    data = recv_msg(_socket)
    if not data:
      return None
  except socket.error:
    return None

  return unpack_packet(data)


def send_packet(_socket: socket.socket, packet: Packet):
  send_msg(_socket, packet.pack())


msg_length = '>I'


def create_msg(msg: bytes):
  return struct.pack(msg_length, len(msg)) + msg


def send_msg(socket: socket.socket, msg: bytes):
  data = create_msg(msg)
  data_sent = 0
  while data_sent < len(data):
    data_sent += socket.send(data[data_sent:])


def recv_msg(socket: socket.socket):
  data = recvall(socket, struct.calcsize(msg_length))
  if not data:
    return None
  length = struct.unpack(msg_length, data)[0]
  return recvall(socket, length)


def recvall(socket: socket.socket, length: int):
  data = bytearray()
  while len(data) < length:
    packet = socket.recv(length - len(data))
    if not packet:
      return None
    data.extend(packet)
  return data


def write_msg(writer: io.BufferedWriter, msg: bytes):
  writer.write(create_msg(msg))
  writer.flush()


def read_msg(reader: io.BufferedReader):
  data = readall(reader, struct.calcsize(msg_length))
  if not data:
    return None
  length = struct.unpack(msg_length, data)[0]
  return readall(reader, length)


def readall(reader: io.BufferedReader, length: int):
  data = bytearray()
  while len(data) < length:
    packet = reader.read(length - len(data))
    if not packet:
      return None
    data.extend(packet)
  return data
