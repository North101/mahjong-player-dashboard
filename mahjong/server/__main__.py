from mahjong.poll import Poll
from mahjong.server import Server
from mahjong.client import Client


def main():
  try:
    poll = Poll()
    server = Server(poll, ('127.0.0.1', 1246))
    server.start()
    client = Client(poll, ('127.0.0.1', 1246))
    client.start()
    while True:
      poll.poll()
  finally:
    poll.close()


if __name__ == '__main__':
  main()
