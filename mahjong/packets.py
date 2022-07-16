import socket
import struct
from typing import *

from mahjong.wind import Wind


def unpack_id(data) -> int:
  return struct.unpack_from('I', data)[0]


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


class RiichiClientPacket(Packet):
  fmt = struct.Struct('I')
  id = 2

  def pack(self) -> bytes:
    return self.fmt.pack(self.id)

  @classmethod
  def unpack(self, data: bytes):
    id,  = self.fmt.unpack(data)
    if id != self.id:
      raise ValueError(id)
    return RiichiClientPacket()

  def __repr__(self) -> str:
    return f'[{self.id}]: {self.__class__.__name__}()'


class TsumoClientPacket(Packet):
  fmt = struct.Struct('III')
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
    return TsumoClientPacket(dealer_points, points)

  def __repr__(self) -> str:
    return f'[{self.id}]: {self.__class__.__name__}({self.dealer_points}, {self.points})'


class RonClientPacket(Packet):
  fmt = struct.Struct('III')
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
    return RonClientPacket(list(Wind)[from_wind], points)

  def __repr__(self) -> str:
    return f'[{self.id}]: {self.__class__.__name__}({self.from_wind, self.points})'


class DrawClientPacket(Packet):
  fmt = struct.Struct('I?')
  id = 5

  def __init__(self, tenpai: bool):
    self.tenpai = tenpai

  def pack(self) -> bytes:
    return self.fmt.pack(self.id, self.tenpai)

  @classmethod
  def unpack(self, data: bytes):
    id, tenpai = self.fmt.unpack(data)
    if id != self.id:
      raise ValueError(id)
    return DrawClientPacket(tenpai)

  def __repr__(self) -> str:
    return f'[{self.id}]: {self.__class__.__name__}({self.tenpai})'


class PlayerStruct(Struct):
  fmt = struct.Struct('i?')

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


class PlayerGameStateServerPacket(Packet):
  fmt = struct.Struct('IIII')
  id = 6

  def __init__(self, hand: int, repeat: int, player_index: int, players: List[PlayerStruct]):
    self.hand = hand
    self.repeat = repeat
    self.player_index = player_index
    self.players = players

  def pack(self) -> bytes:
    data = self.fmt.pack(self.id, self.hand,
                         self.repeat, self.player_index)
    for player in self.players:
      data += PlayerStruct(player.points, player.riichi).pack()
    return data

  @classmethod
  def unpack(self, data: bytes, offset=0):
    id, hand, repeat, player_index = self.fmt.unpack_from(data, offset)
    offset += self.fmt.size

    players: List[PlayerStruct] = []
    for _ in range(len(Wind)):
      players.append(PlayerStruct.unpack(data, offset))
      offset += PlayerStruct.size()

    if id != self.id:
      raise ValueError(id)
    return PlayerGameStateServerPacket(hand, repeat, player_index, players)

  @classmethod
  def size(self):
    return self.fmt.size + (PlayerStruct.size() * len(Wind))

  def __repr__(self) -> str:
    return f'[{self.id}]: {self.__class__.__name__}({self.hand, self.repeat, self.player_index, self.players})'


class DrawServerPacket(Packet):
  fmt = struct.Struct('I')
  id = 8

  def pack(self) -> bytes:
    return self.fmt.pack(self.id)

  @classmethod
  def unpack(self, data: bytes):
    id, = self.fmt.unpack(data)

    if id != self.id:
      raise ValueError(id)
    return DrawServerPacket()


packets: List[Packet] = [
    RiichiClientPacket,
    TsumoClientPacket,
    RonClientPacket,
    DrawClientPacket,

    PlayerGameStateServerPacket,
    DrawServerPacket,
]


def find_packet(id) -> Packet:
  for packet in packets:
    if packet.id == id:
      return packet

  raise ValueError(id)


def unpack_packet(data) -> Packet:
  id = unpack_id(data)
  return find_packet(id).unpack(data)


def read_packet(_socket: socket.socket) -> Packet:
  try:
    data = recv_msg(_socket)
    if not data:
      return None
  except socket.error as e:
    return None

  return unpack_packet(data)


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
