# Poker hand evaluator, shared by Caribbean Stud and Ultimate Texas Hold'em (D-008).
# Pure logic: no `machine` import. Cards are the ints from cards.py (rank = c % 13, 0 = ace).
#
# evaluate(cards) takes 5 to 7 cards and returns a tuple that compares correctly between hands:
# (category, tiebreak...) where category is one of the constants below and the tiebreak ranks use
# ace = 14 (ace = 1 only in the 5-high straight). Bigger tuple = better hand.

HIGH_CARD, PAIR, TWO_PAIR, TRIPS, STRAIGHT, FLUSH, FULL_HOUSE, QUADS, STRAIGHT_FLUSH, ROYAL_FLUSH = range(10)

NAMES = ('high card', 'pair', 'two pair', 'three of a kind', 'straight', 'flush',
         'full house', 'four of a kind', 'straight flush', 'royal flush')


def rank_value(card):
    """2..14, ace high."""
    r = card % 13
    return 14 if r == 0 else r + 1


def evaluate5(cards):
    """Exactly five cards. Returns (category, tiebreak ranks...)."""
    vals = sorted([rank_value(c) for c in cards], reverse=True)
    flush = True
    s0 = cards[0] // 13
    for c in cards:
        if c // 13 != s0:
            flush = False
            break
    # group by count
    counts = {}
    for v in vals:
        counts[v] = counts.get(v, 0) + 1
    groups = sorted(counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)   # (rank, count)
    distinct = len(groups)
    straight_high = 0
    if distinct == 5:
        if vals[0] - vals[4] == 4:
            straight_high = vals[0]
        elif vals == [14, 5, 4, 3, 2]:
            straight_high = 5
    if straight_high and flush:
        if straight_high == 14:
            return (ROYAL_FLUSH, 14)
        return (STRAIGHT_FLUSH, straight_high)
    if groups[0][1] == 4:
        return (QUADS, groups[0][0], groups[1][0])
    if groups[0][1] == 3 and groups[1][1] == 2:
        return (FULL_HOUSE, groups[0][0], groups[1][0])
    if flush:
        return (FLUSH,) + tuple(vals)
    if straight_high:
        return (STRAIGHT, straight_high)
    if groups[0][1] == 3:
        return (TRIPS, groups[0][0], groups[1][0], groups[2][0])
    if groups[0][1] == 2 and groups[1][1] == 2:
        return (TWO_PAIR, groups[0][0], groups[1][0], groups[2][0])
    if groups[0][1] == 2:
        return (PAIR, groups[0][0], groups[1][0], groups[2][0], groups[3][0])
    return (HIGH_CARD,) + tuple(vals)


def _combos5(cards):
    n = len(cards)
    for a in range(n - 4):
        for b in range(a + 1, n - 3):
            for c in range(b + 1, n - 2):
                for d in range(c + 1, n - 1):
                    for e in range(d + 1, n):
                        yield (cards[a], cards[b], cards[c], cards[d], cards[e])


def evaluate(cards):
    """Best five-card hand from 5, 6 or 7 cards."""
    if len(cards) == 5:
        return evaluate5(cards)
    if len(cards) < 5:
        raise ValueError('need at least five cards')
    best = None
    for five in _combos5(list(cards)):
        v = evaluate5(five)
        if best is None or v > best:
            best = v
    return best


def name(value):
    """Plain name of an evaluate() result, e.g. 'two pair'."""
    return NAMES[value[0]]


def compare(a, b):
    """1 if hand value a beats b, -1 if it loses, 0 for a tie."""
    if a > b:
        return 1
    if a < b:
        return -1
    return 0
