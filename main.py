from badger_ui.base import app_runner


def start():
  from mahjong2040.app import MyApp

  app_runner.app = MyApp(1246)
  try:
    while True:
      app_runner.update()
  finally:
    app_runner.app.close()


if __name__ == '__main__':
  start()
