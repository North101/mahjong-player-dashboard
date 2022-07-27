import socket

from mahjong_dashboard.packets import GameDrawClientPacket, GameStateServerPacket, Packet
from mahjong_dashboard.shared import parseTenpai, write
from .shared import GameReconnectClientState


class GameDrawClientState(GameReconnectClientState):
  def __init__(self, client):
    self.client = client

    self.print()

  def on_server_packet(self, server: socket.socket, packet: Packet):
    from .game import GameClientState

    super().on_server_packet(server, packet)
    if isinstance(packet, GameStateServerPacket):
      self.state = GameClientState(self.client, packet)

  def on_input(self, input: str):
    value = input.split()
    if not value:
      return

    tenpai = parseTenpai(value[0].lower())
    if tenpai is not None:
      self.send_packet(GameDrawClientPacket(tenpai))
    else:
      self.print()

  def print(self):
    write('Tenpai? [Yes/No]', input=True)
