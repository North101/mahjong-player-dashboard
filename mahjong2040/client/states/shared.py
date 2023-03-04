from mahjong2040.packets import (
    DrawServerPacket,
    GameStateServerPacket,
    Packet,
    RonWindServerPacket,
)

from .base import ClientState


class GameReconnectClientState(ClientState):
  def on_server_packet(self, packet: Packet) -> bool:
    if isinstance(packet, GameStateServerPacket):
      from .game import GameClientState
      self.child = GameClientState(self.client, packet.game_state)
      return True

    elif isinstance(packet, DrawServerPacket):
      from .game_draw import GameDrawClientState
      self.child = GameDrawClientState(self.client, packet.tenpai)
      return True

    elif isinstance(packet, RonWindServerPacket):
      from .game_ron_score import GameRonScoreClientState
      self.child = GameRonScoreClientState(self.client, packet.from_wind)
      return True

    return super().on_server_packet(packet)