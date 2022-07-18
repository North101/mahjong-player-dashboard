import socket
import struct
from typing import Generic, List, Type, TypeVar

from mahjong.shared import GamePlayerMixin, GamePlayerTuple, GameState, TenpaiState
from mahjong.wind import Wind


class Struct:
  fmt: struct.Struct

  def pack(self) -> bytes:
    raise NotImplementedError()

  @classmethod
  def unpack(self, data: bytes):
    raise NotImplementedError()

  @classmethod
  def size(self):
    return self.fmt.size


class Packet(Struct):
  id: int


class GameRiichiClientPacket(Packet):
  fmt = struct.Struct('B')
  id = 2

  def pack(self) -> bytes:
    return self.fmt.pack(self.id)

  @classmethod
  def unpack(self, data: bytes):
    id, = self.fmt.unpack(data)
    if id != self.id:
      raise ValueError(id)
    return GameRiichiClientPacket()

  def __repr__(self) -> str:
    return f'[{self.id}]: {self.__class__.__name__}()'


class GameTsumoClientPacket(Packet):
  fmt = struct.Struct('BHH')
  id = 3

  def __init__(self, dealer_points, points):
    self.dealer_points = dealer_points
    self.points = points

  def pack(self) -> bytes:
    return self.fmt.pack(self.id, self.dealer_points, self.points)

  @classmethod
  def unpack(self, data: bytes):
    id, dealer_points, points = self.fmt.unpack(data)
    if id != self.id:
      raise ValueError(id)
    return GameTsumoClientPacket(dealer_points, points)

  def __repr__(self) -> str:
    return f'[{self.id}]: {self.__class__.__name__}({self.dealer_points}, {self.points})'


class GameRonClientPacket(Packet):
  fmt = struct.Struct('BBH')
  id = 4

  def __init__(self, from_wind: Wind, points: int):
    self.from_wind = from_wind
    self.points = points

  def pack(self) -> bytes:
    return self.fmt.pack(self.id, self.from_wind, self.points)

  @classmethod
  def unpack(self, data: bytes):
    id, from_wind, points = self.fmt.unpack(data)
    if id != self.id:
      raise ValueError(id)
    return GameRonClientPacket(Wind(from_wind), points)

  def __repr__(self) -> str:
    return f'[{self.id}]: {self.__class__.__name__}({self.from_wind, self.points})'


class GameDrawClientPacket(Packet):
  fmt = struct.Struct('BB')
  id = 5

  def __init__(self, tenpai: TenpaiState):
    self.tenpai = tenpai

  def pack(self) -> bytes:
    return self.fmt.pack(self.id, self.tenpai.value)

  @classmethod
  def unpack(self, data: bytes):
    id, tenpai = self.fmt.unpack(data)
    if id != self.id:
      raise ValueError(id)
    return GameDrawClientPacket(TenpaiState(tenpai))

  def __repr__(self) -> str:
    return f'[{self.id}]: {self.__class__.__name__}({self.tenpai})'


class SetupSelectWindClientPacket(Packet):
  fmt = struct.Struct('BB')
  id = 6

  def __init__(self, wind: Wind):
    self.wind = wind

  def pack(self) -> bytes:
    return self.fmt.pack(self.id, self.wind)

  @classmethod
  def unpack(self, data: bytes):
    id, wind = self.fmt.unpack(data)

    if id != self.id:
      raise ValueError(id)
    return SetupSelectWindClientPacket(Wind(wind))


class PlayerStruct(Struct, GamePlayerMixin):
  fmt = struct.Struct('H?')

  def __init__(self, points: int, riichi: bool) -> None:
    self.points = points
    self.riichi = riichi

  def pack(self):
    return self.fmt.pack(self.points, self.riichi)

  @classmethod
  def unpack(self, data: bytes, offset=0):
    points, riichi = self.fmt.unpack_from(data, offset)
    return PlayerStruct(points, riichi)

  def __repr__(self) -> str:
    return f'{self.__class__.__name__}({self.points}, {self.riichi})'


T = TypeVar('T', bound=GamePlayerMixin)


class GameStateServerPacket(Packet, Generic[T]):
  fmt = struct.Struct('BHHHHB')
  id = 7

  def __init__(self, game_state: GameState, player_index: int, players: GamePlayerTuple[T]):
    self.game_state = game_state
    self.player_index = player_index
    self.players = players

  def pack(self) -> bytes:
    data = self.fmt.pack(
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
    id, hand, repeat, bonus_honba, bonus_riichi, player_index = self.fmt.unpack_from(
        data, offset)
    game_state = GameState(hand, repeat, bonus_honba, bonus_riichi)

    players = GamePlayerTuple(
        PlayerStruct.unpack(data, self.fmt.size + (PlayerStruct.size() * 0)),
        PlayerStruct.unpack(data, self.fmt.size + (PlayerStruct.size() * 1)),
        PlayerStruct.unpack(data, self.fmt.size + (PlayerStruct.size() * 2)),
        PlayerStruct.unpack(data, self.fmt.size + (PlayerStruct.size() * 3)),
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
  fmt = struct.Struct('B')
  id = 8

  def pack(self) -> bytes:
    return self.fmt.pack(self.id)

  @classmethod
  def unpack(self, data: bytes):
    id, = self.fmt.unpack(data)

    if id != self.id:
      raise ValueError(id)
    return GameDrawServerPacket()


class GameRonServerPacket(Packet):
  fmt = struct.Struct('BB')
  id = 9

  def __init__(self, from_wind: Wind):
    self.from_wind = from_wind

  def pack(self) -> bytes:
    return self.fmt.pack(self.id, self.from_wind)

  @classmethod
  def unpack(self, data: bytes):
    id, from_wind = self.fmt.unpack(data)

    if id != self.id:
      raise ValueError(id)
    return GameRonServerPacket(Wind(from_wind))


class SetupSelectWindServerPacket(Packet):
  fmt = struct.Struct('BB')
  id = 10

  def __init__(self, wind: Wind):
    self.wind = wind

  def pack(self) -> bytes:
    return self.fmt.pack(self.id, self.wind)

  @classmethod
  def unpack(self, data: bytes):
    id, wind = self.fmt.unpack(data)

    if id != self.id:
      raise ValueError(id)
    return SetupSelectWindServerPacket(Wind(wind))


class SetupConfirmWindServerPacket(Packet):
  fmt = struct.Struct('BB')
  id = 11

  def __init__(self, wind: Wind):
    self.wind = wind

  def pack(self) -> bytes:
    return self.fmt.pack(self.id, self.wind)

  @classmethod
  def unpack(self, data: bytes):
    id, wind = self.fmt.unpack(data)

    if id != self.id:
      raise ValueError(id)
    return SetupConfirmWindServerPacket(Wind(wind))


class SetupNotEnoughServerPacket(Packet):
  fmt = struct.Struct('B')
  id = 12

  def pack(self) -> bytes:
    return self.fmt.pack(self.id)

  @classmethod
  def unpack(self, data: bytes):
    id, = self.fmt.unpack(data)

    if id != self.id:
      raise ValueError(id)
    return SetupNotEnoughServerPacket()


class LobbyPlayersServerPacket(Packet):
  fmt = struct.Struct('BHH')
  id = 13

  def __init__(self, count: int, max_players: int):
    self.count = count
    self.max_players = max_players

  def pack(self) -> bytes:
    return self.fmt.pack(self.id, self.count, self.max_players)

  @classmethod
  def unpack(self, data: bytes):
    id, count, max_players = self.fmt.unpack(data)

    if id != self.id:
      raise ValueError(id)
    return LobbyPlayersServerPacket(count, max_players)


packets: List[Type[Packet]] = [
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


msg_length = struct.Struct('>I')


def send_msg(socket: socket.socket, msg: bytes):
  msg = msg_length.pack(len(msg)) + msg
  socket.sendall(msg)


def recv_msg(socket: socket.socket):
  data = recvall(socket, 4)
  if not data:
    return None
  length = msg_length.unpack(data)[0]
  return recvall(socket, length)


def recvall(socket: socket.socket, length: int):
  data = bytearray()
  while len(data) < length:
    packet = socket.recv(length - len(data))
    if not packet:
      return None
    data.extend(packet)
  return data
