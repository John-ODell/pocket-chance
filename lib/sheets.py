# Sprite sheets (ruling DR-024): one .565 file per family of same-size images, sprites stacked
# vertically, so a scene opens one file and seeks to each sprite (2.9 ms per card measured against
# 6.6 ms from its own file; reel rows 0.26 ms). This module is the single source of truth for the
# converter (which packs John's separate BMPs in this order) and the loader (which seeks by index).
# Pure: no `machine` import. Member order never changes once art is on the board.
#
# Kept small on purpose (HR-F04: every KB of module counts): no name table is built at import;
# member() computes the index from the name, and names() builds a list only when asked (Mac side).

HDR = 4
_RANKS = 'A23456789TJQK'
_SUITS = 'SHDC'

# sheet name -> (sprite width, sprite height, member count)
SHEETS = {
    'cards': (40, 56, 53),         # index = cards.py card int (suit * 13 + rank); 52 = c_back
    'chips': (24, 24, 5),          # chip_1, chip_5, chip_25, chip_100, chip_500
    'banners': (160, 32, 6),       # banner_win, lose, push, bust, blackjack, noqualify (DR-032)
    'icons': (48, 48, 4),          # icon_blackjack, stud, holdem, baccarat (DR-057)
}
_CHIPS = ('1', '5', '25', '100', '500')
_BANNERS = ('win', 'lose', 'push', 'bust', 'blackjack', 'noqualify')
_ICONS = ('blackjack', 'stud', 'holdem', 'baccarat')


def member(name):
    """(sheet, index) for a sprite name, or None when it is a single file (table, logo, ...)."""
    if name.startswith('c_'):
        if name == 'c_back':
            return 'cards', 52
        if len(name) == 4 and name[2] in _RANKS and name[3] in _SUITS:
            return 'cards', _SUITS.index(name[3]) * 13 + _RANKS.index(name[2])
        return None
    for prefix, sheet, names in (('chip_', 'chips', _CHIPS), ('banner_', 'banners', _BANNERS),
                                 ('icon_', 'icons', _ICONS)):
        if name.startswith(prefix):
            rest = name[len(prefix):]
            if rest in names:
                return sheet, names.index(rest)
            return None
    return None


def names(sheet):
    """Member names of a sheet in index order (converter and tests; builds a list)."""
    if sheet == 'cards':
        return ['c_' + r + s for s in _SUITS for r in _RANKS] + ['c_back']
    prefix, items = {'chips': ('chip_', _CHIPS), 'banners': ('banner_', _BANNERS),
                     'icons': ('icon_', _ICONS)}[sheet]
    return [prefix + n for n in items]


def sprite_bytes(sheet):
    w, h, count = SHEETS[sheet]
    return w * h * 2


def offset(sheet, index):
    """Byte offset of sprite `index` inside the sheet file."""
    return HDR + index * sprite_bytes(sheet)


def file_size(sheet):
    w, h, count = SHEETS[sheet]
    return HDR + count * w * h * 2
