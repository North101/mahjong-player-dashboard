def start():
  from mahjong2040.app import MyApp

  app = MyApp('192.168.0.180', 1246)
  app.run()

if __name__ == '__main__':
  start()