import gc

import uasyncio
from mahjong2040.client import Client, RemoteClientServer
from mahjong2040.poll import Poll

import WIFI_CONFIG
from network_manager import NetworkManager


def main():
  poll = Poll()
  address = ('192.168.0.214', 1246)

  try:
    client = Client()
    client.connect(RemoteClientServer(poll, address, client))
    while True:
      poll.poll()
      client.update()
  finally:
    client.close()
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
