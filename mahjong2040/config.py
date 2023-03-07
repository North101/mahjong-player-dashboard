from mahjong2040.shared import IntEnum, Wind


class ModeState(IntEnum):
  HOST = 0
  CLIENT = 1


Mode = ModeState()

def parse_mode(value: str):
  try:
    return Mode.by_name(value.upper())
  except Exception as e:
    print(e)
    return None

def parse_autoconnect(value: str):
  if value.lower() == 'true':
    return True
  elif value.lower() == 'false':
    return False
  return None

def parse_wind(value: str):
  try:
    return Wind.by_name(value.upper())
  except Exception as e:
    print(e)
    return None

def parse_config() -> tuple[int, bool, int]:
  try:
    with open('/config.ini', 'r') as f:
      config = {
        key.strip(): value.strip()
        for key, value in (
          value.split('=', 1)
          for value in f.readlines()
          if '=' in value
        )
      }

    mode = parse_mode(config.get('mode'))
    autoconnect = parse_autoconnect(config.get('autoconnect'))
    select_wind = parse_wind(config.get('wind'))
    return mode, autoconnect, select_wind
  except:
    return None, None, None

mode, autoconnect, select_wind = parse_config()
