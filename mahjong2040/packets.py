import io
import socket
import struct

from mahjong2040.shared import ClientGameState, GamePlayerMixin, GamePlayerTuple, Wind


class Struct:
  fmt: str

  def pack(self) -> bytes:
    raise NotImplementedError()

  @classmethod
  def unpack(cls, data: bytes):
    raise NotImplementedError()

  @classmethod
  def size(cls):
    return struct.calcsize(cls.fmt)


class Packet(Struct):
  id: int

  def __repr__(self) -> str:
    args = ', '.join([
      f'id={self.id}'
    ] + [
      f'{key}={value}'
      for key, value in self.__dict__.items()
    ])
    return f'{self.__class__.__name__}({args})'


class RiichiClientPacket(Packet):
  fmt = 'B'
  id = 1

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id)

  @classmethod
  def unpack(cls, data: bytes):
    id, = struct.unpack(cls.fmt, data)
    if id != cls.id:
      raise ValueError(id)
    return cls()


class TsumoClientPacket(Packet):
  fmt = 'BHI'
  id = 2

  def __init__(self, dealer_points, points):
    self.dealer_points = dealer_points
    self.points = points

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id, self.dealer_points, self.points)

  @classmethod
  def unpack(cls, data: bytes):
    id, dealer_points, points = struct.unpack(cls.fmt, data)
    if id != cls.id:
      raise ValueError(id)
    return cls(dealer_points, points)


class RonWindClientPacket(Packet):
  fmt = 'BB'
  id = 3

  def __init__(self, from_wind: int):
    self.from_wind = from_wind

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id, self.from_wind)

  @classmethod
  def unpack(cls, data: bytes):
    id, from_wind = struct.unpack(cls.fmt, data)
    if id != cls.id:
      raise ValueError(id)
    return cls(from_wind)


class RonScoreClientPacket(Packet):
  fmt = 'BI'
  id = 4

  def __init__(self, points):
    self.points = points

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id, self.points)

  @classmethod
  def unpack(cls, data: bytes):
    id, points = struct.unpack(cls.fmt, data)
    if id != cls.id:
      raise ValueError(id)
    return cls(points)


class DrawClientPacket(Packet):
  fmt = 'BB'
  id = 5

  def __init__(self, tenpai: int):
    self.tenpai = tenpai

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id, self.tenpai)

  @classmethod
  def unpack(cls, data: bytes):
    id, tenpai = struct.unpack(cls.fmt, data)
    if id != cls.id:
      raise ValueError(id)
    return cls(tenpai)


class RedrawClientPacket(Packet):
  fmt = 'B'
  id = 6

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id)

  @classmethod
  def unpack(cls, data: bytes):
    id, = struct.unpack(cls.fmt, data)

    if id != cls.id:
      raise ValueError(id)
    return cls()


class SetupPlayerWindClientPacket(Packet):
  fmt = 'BB'
  id = 7

  def __init__(self, wind: int):
    self.wind = wind

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id, self.wind)

  @classmethod
  def unpack(cls, data: bytes):
    id, wind = struct.unpack(cls.fmt, data)

    if id != cls.id:
      raise ValueError(id)
    return cls(wind)


class PlayerStruct(Struct, GamePlayerMixin):
  fmt = 'IB'

  def __init__(self, points: int, riichi: bool) -> None:
    self.points = points
    self.riichi = riichi

  def pack(self):
    return struct.pack(self.fmt, self.points, 1 if self.riichi else 0)

  @classmethod
  def unpack(cls, data: bytes, offset=0):
    points, riichi = struct.unpack_from(cls.fmt, data, offset)
    return PlayerStruct(points, riichi != 0)


class GameStateServerPacket(Packet):
  fmt = 'BHHHHB'
  id = 101

  def __init__(self, game_state: ClientGameState):
    self.game_state = game_state

  def pack(self) -> bytes:
    data = struct.pack(
        self.fmt,
        self.id,
        self.game_state.hand,
        self.game_state.repeat,
        self.game_state.bonus_honba,
        self.game_state.bonus_riichi,
        self.game_state.player_index,
    )
    for player in self.game_state.players:
      data += PlayerStruct(player.points, player.riichi).pack()
    return data

  @classmethod
  def unpack(cls, data: bytes, offset=0):
    id, hand, repeat, bonus_honba, bonus_riichi, player_index = struct.unpack_from(
        cls.fmt,
        data,
        offset,
    )

    size = struct.calcsize(cls.fmt)
    player_size = PlayerStruct.size()
    players = GamePlayerTuple(
        PlayerStruct.unpack(data, size + (player_size * 0)),
        PlayerStruct.unpack(data, size + (player_size * 1)),
        PlayerStruct.unpack(data, size + (player_size * 2)),
        PlayerStruct.unpack(data, size + (player_size * 3)),
    )
    game_state = ClientGameState(player_index, players, hand, repeat, bonus_honba, bonus_riichi)

    if id != cls.id:
      raise ValueError(id)
    return cls(game_state)

  @classmethod
  def size(cls):
    return struct.calcsize(cls.fmt) + (PlayerStruct.size() * len(Wind))


class DrawServerPacket(Packet):
  fmt = 'BH'
  id = 102

  def __init__(self, tenpai: int):
    self.tenpai = tenpai

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id, self.tenpai)

  @classmethod
  def unpack(cls, data: bytes):
    id, tenpai = struct.unpack(cls.fmt, data)

    if id != cls.id:
      raise ValueError(id)
    return cls(tenpai)


class RedrawServerPacket(Packet):
  fmt = 'B'
  id = 103

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id)

  @classmethod
  def unpack(cls, data: bytes):
    id, = struct.unpack(cls.fmt, data)

    if id != cls.id:
      raise ValueError(id)
    return cls()


class RonWindServerPacket(Packet):
  fmt = 'BB'
  id = 104

  def __init__(self, from_wind: int):
    self.from_wind = from_wind

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id, self.from_wind)

  @classmethod
  def unpack(cls, data: bytes):
    id, from_wind = struct.unpack(cls.fmt, data)

    if id != cls.id:
      raise ValueError(id)
    return cls(from_wind)


class RonScoreServerPacket(Packet):
  fmt = 'BBI'
  id = 105

  def __init__(self, from_wind: int, points: int):
    self.from_wind = from_wind
    self.points = points

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id, self.from_wind, self.points)

  @classmethod
  def unpack(cls, data: bytes):
    id, from_wind, points = struct.unpack(cls.fmt, data)

    if id != cls.id:
      raise ValueError(id)
    return cls(from_wind, points)


class SetupPlayerWindServerPacket(Packet):
  fmt = 'BB'
  id = 106

  def __init__(self, wind: int):
    self.wind = wind

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id, self.wind)

  @classmethod
  def unpack(cls, data: bytes):
    id, wind = struct.unpack(cls.fmt, data)

    if id != cls.id:
      raise ValueError(id)
    return cls(wind)


class ConfirmWindServerPacket(Packet):
  fmt = 'BB'
  id = 107

  def __init__(self, wind: int):
    self.wind = wind

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id, self.wind)

  @classmethod
  def unpack(cls, data: bytes):
    id, wind = struct.unpack(cls.fmt, data)

    if id != cls.id:
      raise ValueError(id)
    return cls(wind)


class SetupPlayerCountErrorServerPacket(Packet):
  fmt = 'B'
  id = 108

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id)

  @classmethod
  def unpack(cls, data: bytes):
    id, = struct.unpack(cls.fmt, data)

    if id != cls.id:
      raise ValueError(id)
    return cls()


class LobbyPlayersServerPacket(Packet):
  fmt = 'BHH'
  id = 109

  def __init__(self, count: int, max_players: int):
    self.count = count
    self.max_players = max_players

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id, self.count, self.max_players)

  @classmethod
  def unpack(cls, data: bytes):
    id, count, max_players = struct.unpack(cls.fmt, data)

    if id != cls.id:
      raise ValueError(id)
    return cls(count, max_players)


class GameReconnectStatusServerPacket(Packet):
  fmt = 'BB'
  id = 110

  def __init__(self, missing_winds: set[int]):
    self.missing_winds = missing_winds

  def pack(self) -> bytes:
    value = 0
    for wind in self.missing_winds:
      value |= (1 << wind)
    return struct.pack(self.fmt, self.id, value)

  @classmethod
  def unpack(cls, data: bytes):
    id, missing_winds = struct.unpack(cls.fmt, data)

    if id != cls.id:
      raise ValueError(id)
    return cls({
        wind
        for wind in range(len(Wind))
        if (missing_winds >> wind & 1) != 0
    })


class BroadcastClientPacket(Packet):
  fmt = 'B'
  id = 200

  def pack(self) -> bytes:
    return struct.pack(self.fmt, self.id)

  @classmethod
  def unpack(cls, data: bytes):
    id, = struct.unpack(cls.fmt, data)

    if id != cls.id:
      raise ValueError(id)
    return cls()


packets: set = {
    SetupPlayerWindClientPacket,
    RiichiClientPacket,
    TsumoClientPacket,
    RonWindClientPacket,
    RonScoreClientPacket,
    DrawClientPacket,
    RedrawClientPacket,

    LobbyPlayersServerPacket,
    SetupPlayerWindServerPacket,
    ConfirmWindServerPacket,
    SetupPlayerCountErrorServerPacket,
    GameStateServerPacket,
    DrawServerPacket,
    RonWindServerPacket,
    RonScoreServerPacket,
    GameReconnectStatusServerPacket,

    BroadcastClientPacket(),
}
assert(len({
    packet.id
    for packet in packets
}) == len(packets))


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
  except OSError:
    return None

  return unpack_packet(data)


def read_packet_from(_socket: socket.socket):
  try:
    data, addr = recv_msg_from(_socket)
    if not data:
      return None, None
  except OSError:
    return None, None

  return unpack_packet(data), addr


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


def recv_msg_from(socket: socket.socket):
  data, addr = socket.recvfrom(32)
  if not data:
    return None, None
  start = struct.calcsize(msg_length)
  end = start + struct.unpack(msg_length, data)[0]
  return data[start:end], addr

