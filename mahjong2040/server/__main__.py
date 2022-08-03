from mahjong2040.client import Client
from mahjong2040.poll import Poll
from mahjong2040.server import Server


def main():
  address = ('127.0.0.1', 1246)
  try:
    poll = Poll()
    server = Server(poll, address)
    server.start()
    client = Client(poll, address)
    client.start()
    while True:
      poll.poll()
      client.render(app, size, offset)
  finally:
    poll.close()


if __name__ == '__main__':
  main()
