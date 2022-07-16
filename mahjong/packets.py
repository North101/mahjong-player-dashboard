import socket
import struct
from typing import *

from mahjong.wind import Wind


def unpack_id(data) -> int:
  return struct.unpack_from('I', data)[0]


class Struct:
  _fmt: str

  def pack(self) -> bytes:
    raise NotImplementedError()

  @classmethod
  def unpack(self, data):
    raise NotImplementedError()

  @classmethod
  def size(self):
    return struct.calcsize(self._fmt)


class Packet(Struct):
  id: int


class RiichiPacket(Packet):
  _fmt = 'I'
  id = 2

  def pack(self) -> bytes:
    return struct.pack(self._fmt, self.id)

  @classmethod
  def unpack(self, data):
    id,  = struct.unpack(self._fmt, data)
    if id != self.id:
      raise ValueError(id)
    return RiichiPacket()

  def __repr__(self) -> str:
    return f'[{self.id}]: {self.__class__.__name__}()'


class TsumoPacket(Packet):
  _fmt = 'III'
  id = 3

  def __init__(self, dealer_points, points):
    self.dealer_points = dealer_points
    self.points = points

  def pack(self) -> bytes:
    return struct.pack(self._fmt, self.id, self.dealer_points, self.points)

  @classmethod
  def unpack(self, data):
    id, dealer_points, points = struct.unpack(self._fmt, data)
    if id != self.id:
      raise ValueError(id)
    return TsumoPacket(dealer_points, points)

  def __repr__(self) -> str:
    return f'[{self.id}]: {self.__class__.__name__}({self.dealer_points}, {self.points})'


class RonPacket(Packet):
  _fmt = 'III'
  id = 4

  def __init__(self, from_wind: Wind, points: int):
    self.from_wind = from_wind
    self.points = points

  def pack(self) -> bytes:
    return struct.pack(self._fmt, self.id, self.from_wind, self.points)

  @classmethod
  def unpack(self, data):
    id, from_wind, points = struct.unpack(self._fmt, data)
    if id != self.id:
      raise ValueError(id)
    return RonPacket(list(Wind)[from_wind], points)

  def __repr__(self) -> str:
    return f'[{self.id}]: {self.__class__.__name__}({self.from_wind, self.points})'


class DrawPacket(Packet):
  _fmt = 'I?'
  id = 5

  def __init__(self, draw: bool):
    self.draw = draw

  def pack(self) -> bytes:
    return struct.pack(self._fmt, self.id, self.draw)

  @classmethod
  def unpack(self, data):
    id, draw = struct.unpack(self._fmt, data)
    if id != self.id:
      raise ValueError(id)
    return DrawPacket(draw)

  def __repr__(self) -> str:
    return f'[{self.id}]: {self.__class__.__name__}({self.draw})'


class PlayerStruct(Struct):
  _fmt = 'i?'

  def __init__(self, points: int, riichi: bool) -> None:
    self.points = points
    self.riichi = riichi

  def pack(self):
    return struct.pack(self._fmt, self.points, self.riichi)

  @classmethod
  def unpack(self, data, offset=0):
    points, riichi = struct.unpack_from(self._fmt, data, offset)
    return PlayerStruct(points, riichi)

  @classmethod
  def size(self):
    return struct.calcsize(self._fmt)

  def __repr__(self) -> str:
    return f'{self.__class__.__name__}({self.points}, {self.riichi})'


class PlayerGameStatePacket(Packet):
  _fmt = 'IIII'
  id = 0

  def __init__(self, hand: int, repeat: int, player_index: int, players: List[PlayerStruct]):
    self.hand = hand
    self.repeat = repeat
    self.player_index = player_index
    self.players = players

  def pack(self) -> bytes:
    data = struct.pack(self._fmt, self.id, self.hand,
                       self.repeat, self.player_index)
    for player in self.players:
      data += PlayerStruct(player.points, player.riichi).pack()
    return data

  @classmethod
  def unpack(self, data, offset=0):
    id, hand, repeat, player_index = struct.unpack_from(
        self._fmt, data, offset)
    offset += struct.calcsize(self._fmt)

    players: List[PlayerStruct] = []
    for _ in range(len(Wind)):
      players.append(PlayerStruct.unpack(data, offset))
      offset += PlayerStruct.size()

    if id != self.id:
      raise ValueError(id)
    return PlayerGameStatePacket(hand, repeat, player_index, players)

  @classmethod
  def size(self):
    return struct.calcsize(self._fmt) + (PlayerStruct.size() * len(Wind))

  def __repr__(self) -> str:
    return f'[{self.id}]: {self.__class__.__name__}({self.hand, self.repeat, self.player_index, self.players})'


packets: List[Packet] = [
    PlayerGameStatePacket,
    RiichiPacket,
    TsumoPacket,
    RonPacket,
    DrawPacket,
]


def find_packet(id):
  for packet in packets:
    if packet.id == id:
      return packet

  raise ValueError(id)


def unpack_packet(data) -> Packet:
  id = unpack_id(data)
  for packet in packets:
    if packet.id == id:
      return packet.unpack(data)

  raise ValueError(id)


def read_packet(_socket: socket.socket) -> Packet:
  try:
    data = recv_msg(_socket)
    if not data:
      return None
  except socket.error as e:
    return None

  return unpack_packet(data)


def send_msg(sock: socket.socket, msg: bytes):
  msg = struct.pack('>I', len(msg)) + msg
  sock.sendall(msg)


def recv_msg(sock: socket.socket):
  raw_msglen = recvall(sock, 4)
  if not raw_msglen:
    return None
  msglen = struct.unpack('>I', raw_msglen)[0]
  return recvall(sock, msglen)


def recvall(sock: socket.socket, n: int):
  data = bytearray()
  while len(data) < n:
    packet = sock.recv(n - len(data))
    if not packet:
      return None
    data.extend(packet)
  return data
