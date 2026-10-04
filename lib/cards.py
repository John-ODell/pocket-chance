# Cards and shoe. Pure logic: no `machine` import, runs under CPython and MicroPython.
#
# A card is a small int 0..51:  rank = card % 13  (0=A, 1=2 ... 8=9, 9=T, 10=J, 11=Q, 12=K)
#                               suit = card // 13 (0=S, 1=H, 2=D, 3=C)
# card_name() gives the asset name used in assets/ASSETS.md, e.g. 'AS', 'TH', '7C'.

RANKS = 'A23456789TJQK'
SUITS = 'SHDC'


def card_rank(card):
    return card % 13


def card_suit(card):
    return card // 13


def card_name(card):
    return RANKS[card % 13] + SUITS[card // 13]


def card_from_name(name):
    return SUITS.index(name[1]) * 13 + RANKS.index(name[0])


def card_points(card):
    """Hard value of one card: ace counts 1, faces 10."""
    r = card % 13
    if r >= 9:
        return 10
    return r + 1


def hand_value(cards):
    """Return (total, soft). `soft` is True when an ace is being counted as 11."""
    total = 0
    aces = 0
    for c in cards:
        total += card_points(c)
        if c % 13 == 0:
            aces += 1
    if aces and total + 10 <= 21:
        return total + 10, True
    return total, False


class Shoe:
    """One or more 52-card decks, shuffled with Fisher-Yates.

    rng      object with randrange(n), e.g. the `random` module or random.Random(seed).
             (MicroPython's random has no shuffle(), so we do our own.)
    penetration  fraction of the shoe that may be dealt before needs_shuffle() is True.
    stacked  optional list of cards to deal in exactly this order (for tests).
             Dealing past the end of a stacked shoe raises IndexError.
    """

    def __init__(self, decks, rng, penetration=0.75, stacked=None):
        self.decks = decks
        self.rng = rng
        self.penetration = penetration
        self.cards = bytearray(52 * decks)
        self.pos = 0
        self.stacked = stacked is not None
        if self.stacked:
            self.cards = bytearray(stacked)
        else:
            self.shuffle()

    def shuffle(self):
        n = 52 * self.decks
        cards = bytearray(n)
        for i in range(n):
            cards[i] = i % 52
        rng = self.rng
        i = n - 1
        while i > 0:
            j = rng.randrange(i + 1)
            t = cards[i]
            cards[i] = cards[j]
            cards[j] = t
            i -= 1
        self.cards = cards
        self.pos = 0

    def remaining(self):
        return len(self.cards) - self.pos

    def needs_shuffle(self):
        if self.stacked:
            return False
        return self.pos >= len(self.cards) * self.penetration

    def draw(self):
        if self.pos >= len(self.cards):
            if self.stacked:
                raise IndexError('stacked shoe is empty')
            self.shuffle()  # safety net; penetration should prevent this
        c = self.cards[self.pos]
        self.pos += 1
        return c
