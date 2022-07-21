from mahjong_dashboard.client import Client
from mahjong_dashboard.poll import Poll


def main():
  address = ('127.0.0.1', 1246)
  try:
    poll = Poll()
    client = Client(poll, address)
    client.start()
    while True:
      poll.poll()
      client.update_display()
  finally:
    poll.close()


if __name__ == '__main__':
  main()
