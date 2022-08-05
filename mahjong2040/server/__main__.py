import badger2040
from mahjong2040.client import Client
from mahjong2040.poll import Poll
from mahjong2040.server import Server

def main():
  display = badger2040.Badger2040()
  display.update_speed(badger2040.UPDATE_TURBO)

  address = ('127.0.0.1', 1246)
  poll = Poll()
  try:
    server = Server(poll, address)
    server.start()
    client = Client(poll, address)
    client.start()
    while True:
      poll.poll()
      client.update()
  finally:
    poll.close()

if __name__ == '__main__':
  main()
