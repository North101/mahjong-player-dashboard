import typing

from mahjong2040.packets import Packet
from mahjong2040.shared import RIICHI_POINTS, GamePlayerMixin

if typing.TYPE_CHECKING:
  from mahjong2040.server import Server

  from .shared import ServerClient


class GamePlayer(GamePlayerMixin):
  def __init__(self, client: ServerClient, points: int, riichi: bool = False):
    self.client = client
    self.points = points
    self.riichi = riichi

  def declare_riichi(self):
    if not self.riichi:
      self.riichi = True
      self.points -= RIICHI_POINTS

  def take_points(self, other: 'GamePlayerMixin', points: int):
    self.points += points
    other.points -= points

  def send_packet(self, packet: Packet):
    self.client.send_packet(packet)


class ServerState:
  def __init__(self, server: Server):
    print(self.__class__.__name__)
    self.server = server

  def init(self):
    pass

  @property
  def clients(self):
    return self.server.clients

  @property
  def child(self):
    return self.server.child

  @child.setter
  def child(self, child: 'ServerState'):
    self.server.child = child

  def on_client_join(self, client: ServerClient):
    pass

  def on_client_leave(self, client: ServerClient):
    pass

  def on_client_packet(self, client: ServerClient, packet: Packet):
    print(repr(packet))
