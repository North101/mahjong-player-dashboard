from mahjong.client import Client
from mahjong.poll import Poll
from mahjong.server import Server


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
      client.update_display()
  finally:
    poll.close()


if __name__ == '__main__':
  main()
