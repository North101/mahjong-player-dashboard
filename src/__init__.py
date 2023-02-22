from mahjong2040.app import MyApp


def start():
  app = MyApp('192.168.0.138', 1246)
  app.run()

if __name__ == '__main__':
  start()