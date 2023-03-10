import socket
import struct

from .shared import Address, ClientGameState, GamePlayerMixin, Wind


class Struct:
  fmt: str

  @classmethod
  def from_data(cls, buffer: bytes, offset=0):
    offset, data = cls.unpack(buffer, offset)
    return cls(*data)

  def pack_data(self):
    return ()

  def pack(self, buffer: bytearray, offset=0) -> int:
    struct.pack_into(self.fmt, buffer, offset, *self.pack_data())
    return offset + struct.calcsize(self.fmt)

  @staticmethod
  def _unpack(cls, buffer: bytes, offset=0) -> tuple[int, tuple]:
    return offset + struct.calcsize(cls.fmt), struct.unpack_from(cls.fmt, buffer, offset)

  @classmethod
  def unpack(cls, buffer: bytes, offset=0):
    data = cls._unpack(cls, buffer, offset)
    return data

  @staticmethod
  def _size(cls):
    return struct.calcsize(cls.fmt)

  @classmethod
  def size(cls):
    return cls._size(cls)

  def __repr__(self) -> str:
    args = ', '.join([
        f'{key}={value}'
        for key, value in self.__dict__.items()
    ])
    return f'{self.__class__.__name__}({args})'


class LengthStruct(Struct):
  fmt = '>I'

  def __init__(self, length: int) -> None:
    self.length = length

  def pack_data(self) -> tuple:
    return (self.length,)


class PlayerStruct(Struct, GamePlayerMixin):
  fmt = 'hB'

  def __init__(self, points: int, riichi: bool) -> None:
    self.points = points
    self.riichi = riichi

  def pack_data(self) -> tuple:
    return (self.points, 1 if self.riichi else 0,)

  @staticmethod
  def _unpack(cls, buffer: bytes, offset=0):
    offset, (points, riichi) = super()._unpack(cls, buffer, offset)
    return offset, (points, riichi != 0)


class GameStateStruct(Struct):
  fmt = 'HBBBBB'

  def __init__(self, game_state: ClientGameState) -> None:
    self.game_state = game_state

  def pack_data(self) -> tuple:
    return (
        self.game_state.starting_points,
        self.game_state.hand,
        self.game_state.repeat,
        self.game_state.bonus_honba,
        self.game_state.bonus_riichi,
        self.game_state.player_index,
    )

  def pack(self, buffer: bytearray, offset=0):
    offset = super().pack(buffer, offset)
    for player in self.game_state.players:
      offset = PlayerStruct(player.points, player.riichi).pack(buffer, offset)
    return offset

  @staticmethod
  def _unpack(cls, buffer: bytes, offset=0):
    offset, (
        starting_points,
        hand,
        repeat,
        bonus_honba,
        bonus_riichi,
        player_index,
    ) = super()._unpack(cls, buffer, offset)

    players: list[PlayerStruct] = []
    for _ in range(4):
      offset, data = PlayerStruct.unpack(buffer, offset)
      players.append(PlayerStruct(*data))

    return offset, (
        ClientGameState(
            player_index,
            tuple(players),
            starting_points,
            hand,
            repeat,
            bonus_honba,
            bonus_riichi,
        ),
    )

  @classmethod
  def size(cls):
    return super()._size(cls) + (PlayerStruct.size() * len(Wind))


class PacketIdStruct(Struct):
  fmt = 'B'

  def __init__(self, id: int):
    self.id = id

  def pack_data(self) -> tuple:
    return self.id,


class Packet(Struct):
  id: int


class BroadcastClientPacket(Packet):
  fmt = ''
  id = 0


class RiichiClientPacket(Packet):
  fmt = ''
  id = 1


class TsumoClientPacket(Packet):
  fmt = 'bb'
  id = 2

  def __init__(self, han: int, fu_index: int):
    self.han = han
    self.fu_index = fu_index

  def pack_data(self) -> tuple:
    return (self.han, self.fu_index,)


class RonWindClientPacket(Packet):
  fmt = 'B'
  id = 3

  def __init__(self, from_wind: int):
    self.from_wind = from_wind

  def pack_data(self) -> tuple:
    return (self.from_wind,)


class RonScoreClientPacket(Packet):
  fmt = 'bb'
  id = 4

  def __init__(self, han: int, fu_index: int):
    self.han = han
    self.fu_index = fu_index

  def pack_data(self) -> tuple:
    return (self.han, self.fu_index,)


class DrawClientPacket(Packet):
  fmt = 'B'
  id = 5

  def __init__(self, tenpai: int):
    self.tenpai = tenpai

  def pack_data(self) -> tuple:
    return (self.tenpai,)


class RedrawClientPacket(Packet):
  fmt = ''
  id = 6


class SetupPlayerWindClientPacket(Packet):
  fmt = 'B'
  id = 7

  def __init__(self, wind: int):
    self.wind = wind

  def pack_data(self) -> tuple:
    return (self.wind,)


class BroadcastServerPacket(Packet):
  fmt = ''
  id = 100


class GameStateServerPacket(Packet):
  fmt = ''
  id = 101

  def __init__(self, game_state: ClientGameState):
    self.game_state = game_state

  def pack(self, buffer: bytearray, offset=0):
    offset = super().pack(buffer, offset)
    offset = GameStateStruct(self.game_state).pack(buffer, offset)
    return offset

  @staticmethod
  def _unpack(cls, buffer: bytes, offset=0):
    offset, data = super()._unpack(cls, buffer, offset)
    offset, game_state = GameStateStruct.unpack(buffer, offset)
    return offset, data + game_state

  @staticmethod
  def _size(cls):
    return super()._size(cls) + GameStateStruct.size()


class DrawTenpaiServerPacket(Packet):
  fmt = 'B'
  id = 102

  def __init__(self, tenpai: int):
    self.tenpai = tenpai

  def pack_data(self) -> tuple:
    return (self.tenpai,)


class RedrawServerPacket(Packet):
  fmt = ''
  id = 103


class RonWindServerPacket(Packet):
  fmt = 'BB'
  id = 104

  def __init__(self, from_wind: int, is_dealer: bool):
    self.from_wind = from_wind
    self.is_dealer = is_dealer

  def pack_data(self) -> tuple:
    return (self.from_wind, 1 if self.is_dealer else 0)

  @staticmethod
  def _unpack(cls, buffer: bytes, offset=0):
    offset, (from_wind, is_dealer) = super()._unpack(cls, buffer, offset)
    return offset, (from_wind, is_dealer != 0)


class RonScoreServerPacket(Packet):
  fmt = 'Bh'
  id = 105

  def __init__(self, from_wind: int, points: int):
    self.from_wind = from_wind
    self.points = points

  def pack_data(self) -> tuple:
    return (self.from_wind, self.points,)


class SetupPlayerWindServerPacket(Packet):
  fmt = 'B'
  id = 106

  def __init__(self, wind: int):
    self.wind = wind

  def pack_data(self) -> tuple:
    return (self.wind,)


class ConfirmWindServerPacket(Packet):
  fmt = 'B'
  id = 107

  def __init__(self, wind: int):
    self.wind = wind

  def pack_data(self) -> tuple:
    return (self.wind,)


class SetupPlayerCountErrorServerPacket(Packet):
  fmt = ''
  id = 108


class LobbyPlayersServerPacket(Packet):
  fmt = 'BB'
  id = 109

  def __init__(self, count: int, max_players: int):
    self.count = count
    self.max_players = max_players

  def pack_data(self) -> tuple:
    return (self.count, self.max_players,)


class GameReconnectStatusServerPacket(Packet):
  fmt = 'B'
  id = 110

  def __init__(self, missing_winds: set[int]):
    self.missing_winds = missing_winds

  def pack_data(self) -> tuple:
    value = 0
    for wind in self.missing_winds:
      value |= (1 << wind)
    return (value,)

  @staticmethod
  def _unpack(cls, buffer: bytes, offset=0):
    offset, (missing_winds,) = super()._unpack(cls, buffer, offset)

    return offset, ({
        wind
        for wind in range(len(Wind))
        if (missing_winds >> wind & 1) != 0
    },)


class TsumoServerPacket(Packet):
  fmt = 'BBhhhh'
  id = 111

  def __init__(self, tsumo_wind: int, tsumo_hand: int, points: tuple[int, int, int, int], game_state: ClientGameState):
    self.game_state = game_state
    self.tsumo_wind = tsumo_wind
    self.tsumo_hand = tsumo_hand
    self.points = points

  def pack_data(self) -> tuple:
    return (self.tsumo_wind, self.tsumo_hand) + self.points

  def pack(self, buffer: bytearray, offset=0):
    offset = super().pack(buffer, offset)
    offset = GameStateStruct(self.game_state).pack(buffer, offset)
    return offset

  @staticmethod
  def _unpack(cls, buffer: bytes, offset=0):
    offset, (tsumo_wind, tsumo_hand, *points) = super()._unpack(cls, buffer, offset)
    offset, game_state = GameStateStruct.unpack(buffer, offset)
    return offset, (tsumo_wind, tsumo_hand, points) + game_state

  @staticmethod
  def _size(cls):
    return super()._size(cls) + GameStateStruct.size()


class RonServerPacket(Packet):
  fmt = 'BBhhhh'
  id = 112

  def __init__(self, ron_wind: int, ron_hand: int, points: tuple[int, int, int, int], game_state: ClientGameState):
    self.game_state = game_state
    self.ron_wind = ron_wind
    self.ron_hand = ron_hand
    self.points = points

  def pack_data(self) -> tuple:
    return (self.ron_wind, self.ron_hand) + self.points

  def pack(self, buffer: bytearray, offset=0):
    offset = super().pack(buffer, offset)
    offset = GameStateStruct(self.game_state).pack(buffer, offset)
    return offset

  @staticmethod
  def _unpack(cls, buffer: bytes, offset=0):
    offset, (ron_wind, ron_hand, *points) = super()._unpack(cls, buffer, offset)
    offset, game_state = GameStateStruct.unpack(buffer, offset)
    return offset, (ron_wind, ron_hand, points) + game_state

  @staticmethod
  def _size(cls):
    return super()._size(cls) + GameStateStruct.size()


class DrawServerPacket(Packet):
  fmt = 'BBBBBhhhh'
  id = 113

  def __init__(self, draw_hand: int, tenpai: tuple[bool, bool, bool, bool],
               points: tuple[int, int, int, int], game_state: ClientGameState):
    self.draw_hand = draw_hand
    self.tenpai = tenpai
    self.points = points
    self.game_state = game_state

  def pack_data(self) -> tuple:
    tenpai = tuple((
        1 if tenpai else 0
        for tenpai in self.tenpai
    ))
    return (self.draw_hand,) + tenpai + self.points

  def pack(self, buffer: bytearray, offset=0):
    offset = super().pack(buffer, offset)
    offset = GameStateStruct(self.game_state).pack(buffer, offset)
    return offset

  @staticmethod
  def _unpack(cls, buffer: bytes, offset=0):
    offset, (draw_hand, tenpai0, tenpai1, tenpai2, tenpai3, points0, points1,
             points2, points3) = super()._unpack(cls, buffer, offset)
    tenpai = (
        tenpai0 != 0,
        tenpai1 != 0,
        tenpai2 != 0,
        tenpai3 != 0,
    )
    points = (
        points0,
        points1,
        points2,
        points3,
    )
    offset, game_state = GameStateStruct.unpack(buffer, offset)
    return offset, (draw_hand, tenpai, points) + game_state

  @staticmethod
  def _size(cls):
    return super()._size(cls) + GameStateStruct.size()


packets: set = {
    BroadcastClientPacket,
    SetupPlayerWindClientPacket,
    RiichiClientPacket,
    TsumoClientPacket,
    RonWindClientPacket,
    RonScoreClientPacket,
    DrawClientPacket,
    RedrawClientPacket,

    BroadcastServerPacket,
    LobbyPlayersServerPacket,
    SetupPlayerWindServerPacket,
    ConfirmWindServerPacket,
    SetupPlayerCountErrorServerPacket,
    GameStateServerPacket,
    DrawTenpaiServerPacket,
    RonWindServerPacket,
    RonScoreServerPacket,
    GameReconnectStatusServerPacket,
    TsumoServerPacket,
    RonServerPacket,
    DrawServerPacket,
}
assert (len({
    packet.id
    for packet in packets
}) == len(packets))


def find_packet(id):
  for packet in packets:
    if packet.id == id:
      return packet

  raise ValueError(id)


def unpack_packet(buffer: bytes, offset=0) -> Packet:
  offset, (id,) = PacketIdStruct.unpack(buffer, offset)
  return find_packet(id).from_data(buffer, offset)


def send_packet(_socket: socket.socket, packet: Packet):
  size = PacketIdStruct.size() + packet.size()
  buffer = bytearray(LengthStruct.size() + PacketIdStruct.size() + packet.size())
  offset = LengthStruct(size).pack(buffer)
  offset = PacketIdStruct(packet.id).pack(buffer, offset)
  offset = packet.pack(buffer, offset)
  send_data(_socket, buffer)


def send_data(socket: socket.socket, data: bytes):
  data_sent = 0
  while data_sent < len(data):
    data_sent += socket.send(data[data_sent:])


def send_packet_to(_socket: socket.socket, packet: Packet, address: Address):
  size = PacketIdStruct.size() + packet.size()
  buffer = bytearray(LengthStruct.size() + PacketIdStruct.size() + packet.size())
  offset = LengthStruct(size).pack(buffer)
  offset = PacketIdStruct(packet.id).pack(buffer, offset)
  offset = packet.pack(buffer, offset)
  send_data_to(_socket, buffer, address)


def send_data_to(socket: socket.socket, data: bytes, address: Address):
  data_sent = 0
  while data_sent < len(data):
    data_sent += socket.sendto(data[data_sent:], address)


def read_packet(_socket: socket.socket):
  try:
    data = recv_data(_socket)
    if not data:
      return None
  except OSError:
    return None

  return unpack_packet(data)


def recv_data(socket: socket.socket):
  data = recvall(socket, LengthStruct.size())
  if not data:
    return None
  _, (msg_length,) = LengthStruct.unpack(data)
  return recvall(socket, msg_length)


def recvall(socket: socket.socket, length: int):
  data = bytearray()
  while len(data) < length:
    packet = socket.recv(length - len(data))
    if not packet:
      return data
    data.extend(packet)
  return data


def read_packet_from(_socket: socket.socket):
  try:
    data, addr = recv_data_from(_socket)
    if not data:
      return None, None
  except OSError:
    return None, None

  return unpack_packet(data), addr


def recv_data_from(socket: socket.socket):
  length_size = LengthStruct.size()
  data, addr = socket.recvfrom(length_size + PacketIdStruct.size())
  return data[length_size:], addr
