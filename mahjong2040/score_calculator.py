fu_lookup = [
    20,
    25,
    30,
    40,
    50,
    60,
    70,
    80,
    90,
    100,
    110
]

mangan_lookup = {
    'mangan': (120, 80, 40, 20),
    'haneman': (180, 120, 60, 30),
    'baiman': (240, 160, 80, 40),
    'sanbaiman': (360, 240, 120, 60),
    'yakuman': (480, 320, 160, 80)
}

han_lookup = [
    0,
    [
        (0, 0, 0, 0),
        (0, 0, 0, 0),
        (15, 10, 5, 3),
        (20, 13, 7, 4),
        (24, 16, 8, 4),
        (29, 20, 10, 5),
        (34, 23, 12, 6),
        (39, 26, 13, 7),
        (44, 29, 15, 8),
        (48, 32, 16, 8),
        (53, 36, 18, 9)
    ],
    [
        (0, 0, 7, 4),
        (24, 16, 0, 0),
        (29, 20, 10, 5),
        (39, 26, 13, 7),
        (48, 32, 16, 8),
        (58, 39, 20, 10),
        (68, 45, 23, 12),
        (77, 52, 26, 13),
        (87, 58, 29, 15),
        (96, 64, 32, 16),
        (106, 71, 36, 18)
    ],
    [
        (0, 0, 13, 7),
        (48, 32, 16, 8),
        (58, 39, 20, 10),
        (77, 52, 26, 13),
        (96, 64, 32, 16),
        (116, 77, 39, 20),
        'mangan',
        'mangan',
        'mangan',
        'mangan',
        'mangan'
    ],
    [
        (0, 0, 26, 13),
        (96, 64, 32, 16),
        (116, 77, 39, 20),
        'mangan',
        'mangan',
        'mangan',
        'mangan',
        'mangan',
        'mangan',
        'mangan',
        'mangan'
    ],
    'mangan',
    'haneman',
    'haneman',
    'baiman',
    'baiman',
    'baiman',
    'sanbaiman',
    'sanbaiman',
    'yakuman'
]


def calculate_score(han, fu_index) -> tuple[int, int, int, int]:
  if han >= len(han_lookup):
    han = -1
  han_fu_lookup = han_lookup[han]
  if han_fu_lookup == 0:
    return (0, 0, 0, 0)
  elif isinstance(han_fu_lookup, str):
    return mangan_lookup[han_fu_lookup]
  han_fu = han_fu_lookup[fu_index]
  if isinstance(han_fu, str):
    return mangan_lookup[han_fu]
  return han_fu


def tsumo(han: int, fu_index: int, dealer: bool):
  (_, _, dealer_tsumo, non_dealer_tsumo) = calculate_score(han, fu_index)
  return dealer_tsumo if dealer else non_dealer_tsumo


def ron(han: int, fu_index: int, dealer: bool):
  (dealer_ron, non_dealer_ron, _, _) = calculate_score(han, fu_index)
  return dealer_ron if dealer else non_dealer_ron
