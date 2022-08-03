import badger2040
from mahjong2040.client import Client
from mahjong2040.client.states.game import GameClientState
from mahjong2040.packets import PlayerStruct
from mahjong2040.poll import Poll
from mahjong2040.shared import Address, ClientGameState, GamePlayerTuple


def main():
  display = badger2040.Badger2040()
  display.update_speed(badger2040.UPDATE_TURBO)

  address = Address('127.0.0.1', 1246)
  poll = Poll()
  try:
    client = Client(display, poll, address)
    client.child = GameClientState(client, ClientGameState(
        0,
        GamePlayerTuple(
            PlayerStruct(2500, False),
            PlayerStruct(2500, False),
            PlayerStruct(2500, False),
            PlayerStruct(2500, False),
        ),
    ))
    # client.start()
    while True:
      poll.poll()
      client.update()
  finally:
    poll.close()


if __name__ == '__main__':
  main()
