# Sprite sheets (ruling DR-024): one .565 file per family of same-size images, sprites stacked
# vertically, so a scene opens one file and seeks to each sprite (2.9 ms per card measured against
# 6.6 ms from its own file; reel rows 0.26 ms). This list is the single source of truth for the
# converter (which packs John's separate BMPs in this order) and the loader (which seeks by index).
# Pure: no `machine` import. Member order never changes once art is on the board.

HDR = 4

# sheet name -> (sprite width, sprite height, member names in order)
_RANKS = 'A23456789TJQK'
_SUITS = 'SHDC'
CARDS = tuple('c_' + r + s for s in _SUITS for r in _RANKS) + ('c_back',)   # index = cards.py card int; 52 = back

SHEETS = {
    'cards': (40, 56, CARDS),
    'chips': (24, 24, ('chip_1', 'chip_5', 'chip_25', 'chip_100', 'chip_500')),
    'banners': (160, 32, ('banner_win', 'banner_lose', 'banner_push', 'banner_bust', 'banner_blackjack')),
    'icons': (48, 48, ('icon_blackjack', 'icon_slots', 'icon_stud', 'icon_holdem')),
    'symbols': (56, 56, ('sym_cherry', 'sym_lemon', 'sym_orange', 'sym_bell', 'sym_bar', 'sym_seven',
                         'sym_diamond', 'sym_star')),      # slots_rules.SYMBOLS order
}

_MEMBER = {}
for _sheet, (_w, _h, _names) in SHEETS.items():
    for _i, _n in enumerate(_names):
        _MEMBER[_n] = (_sheet, _i)


def member(name):
    """(sheet, index) for a sprite name, or None when it is a single file (table, logo, ...)."""
    return _MEMBER.get(name)


def sprite_bytes(sheet):
    w, h, names = SHEETS[sheet]
    return w * h * 2


def offset(sheet, index):
    """Byte offset of sprite `index` inside the sheet file."""
    return HDR + index * sprite_bytes(sheet)


def file_size(sheet):
    w, h, names = SHEETS[sheet]
    return HDR + len(names) * w * h * 2
