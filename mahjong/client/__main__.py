from mahjong.client import Client
from mahjong.poll import Poll


def main():
  try:
    poll = Poll()
    client = Client(poll, ('127.0.0.1', 1246))
    client.start()
    while True:
      poll.poll()
  finally:
    poll.close()


if __name__ == '__main__':
  main()
