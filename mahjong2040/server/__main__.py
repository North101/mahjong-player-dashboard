import gc

import uasyncio
from mahjong2040.poll import Poll
from mahjong2040.server import Server

import WIFI_CONFIG
from network_manager import NetworkManager


def main():
  address = ('127.0.0.1', 1246)
  poll = Poll()
  try:
    server = Server(poll, address)
    server.start()
    while True:
      poll.poll()
  finally:
    poll.close()


def status_handler(mode, status, ip):
  print(mode, status, ip)
  if status:
    main()
    

if __name__ == '__main__':
  if WIFI_CONFIG.COUNTRY == "":
      raise RuntimeError("You must populate WIFI_CONFIG.py for networking.")
  network_manager = NetworkManager(WIFI_CONFIG.COUNTRY, status_handler=status_handler)
  uasyncio.get_event_loop().run_until_complete(network_manager.client(WIFI_CONFIG.SSID, WIFI_CONFIG.PSK))
  gc.collect()
