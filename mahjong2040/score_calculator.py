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
    'mangan': (12000, 8000, 4000, 2000),
    'haneman': (18000, 12000, 6000, 3000),
    'baiman': (24000, 16000, 8000, 4000),
    'sanbaiman': (36000, 24000, 12000, 6000),
    'yakuman': (48000, 32000, 16000, 8000)
}

han_lookup = [
    0,
    [
        (0, 0, 0, 0),
        (0, 0, 0, 0),
        (1500, 1000, 500, 300),
        (2000, 1300, 700, 400),
        (2400, 1600, 800, 400),
        (2900, 2000, 1000, 500),
        (3400, 2300, 1200, 600),
        (3900, 2600, 1300, 700),
        (4400, 2900, 1500, 800),
        (4800, 3200, 1600, 800),
        (5300, 3600, 1800, 900)
    ],
    [
        (0, 0, 700, 400),
        (2400, 1600, 0, 0),
        (2900, 2000, 1000, 500),
        (3900, 2600, 1300, 700),
        (4800, 3200, 1600, 800),
        (5800, 3900, 2000, 1000),
        (6800, 4500, 2300, 1200),
        (7700, 5200, 2600, 1300),
        (8700, 5800, 2900, 1500),
        (9600, 6400, 3200, 1600),
        (10600, 7100, 3600, 1800)
    ],
    [
        (0, 0, 1300, 700),
        (4800, 3200, 1600, 800),
        (5800, 3900, 2000, 1000),
        (7700, 5200, 2600, 1300),
        (9600, 6400, 3200, 1600),
        (11600, 7700, 3900, 2000),
        'mangan',
        'mangan',
        'mangan',
        'mangan',
        'mangan'
    ],
    [
        (0, 0, 2600, 1300),
        (9600, 6400, 3200, 1600),
        (11600, 7700, 3900, 2000),
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
    elif type(han_fu_lookup) is str:
        return mangan_lookup[han_fu_lookup]
    han_fu = han_fu_lookup[fu_index]
    if type(han_fu) is str:
        return mangan_lookup[han_fu]
    return han_fu


def tsumo(han: int, fu_index: int, dealer: bool):
    (_, _, dealer_tsumo, non_dealer_tsumo) = calculate_score(han, fu_index)
    return dealer_tsumo if dealer else non_dealer_tsumo


def ron(han: int, fu_index: int, dealer: bool):
    (dealer_ron, non_dealer_ron, _, _) = calculate_score(han, fu_index)
    return dealer_ron if dealer else non_dealer_ron
