# Slots rules engine. Pure logic: no `machine` import, runs under CPython and MicroPython.
#
# Three reels, one payline (the centre window of each reel). Each reel is a "virtual strip": a list
# of symbol ids, every stop equally likely, so symbol odds come from how often a symbol appears on
# the strip. The screen scrolls through the strip in order while spinning, so what the player sees
# flying past is the real strip. Strips and the paytable are parameters (DR-017, DR-018 pending).
# Money is whole chips; spin() returns the win for the bet, the caller owns the bankroll.

SYMBOLS = ('cherry', 'lemon', 'orange', 'bell', 'bar', 'seven', 'diamond', 'star')
CHERRY, LEMON, ORANGE, BELL, BAR, SEVEN, DIAMOND, STAR = range(8)


def strip(counts):
    """Build a reel strip from a dict {symbol: stops}, spreading each symbol along the strip so
    neighbouring stops differ (looks right when scrolling)."""
    total = sum(counts.values())
    out = [None] * total
    i = 0
    order = sorted(counts, key=lambda s: -counts[s])
    # place the most common symbol first at even spacing, then fill the gaps with the rest
    for s in order:
        n = counts[s]
        placed = 0
        step = total / n
        pos = 0.0
        while placed < n:
            j = int(pos) % total
            while out[j] is not None:
                j = (j + 1) % total
            out[j] = s
            placed += 1
            pos += step
    return out


class Paytable:
    """three: {symbol: pay per chip bet for three of a kind on the line}.
    cherries: {count: pay} for exactly `count` cherries on the line when no three-of-a-kind hit.
    any_bar: pay for three of (bar, seven, diamond) mixed, when not already three of a kind."""

    def __init__(self, three, cherries=None, any_fruit=None):
        self.three = three
        self.cherries = cherries or {}
        self.any_fruit = any_fruit         # (set of symbols, pay) or None

    def evaluate(self, line, bet):
        """Return (win, label). label names the winning combination, or None."""
        a, b, c = line
        if a == b == c:
            pay = self.three.get(a)
            if pay:
                return pay * bet, 'three ' + SYMBOLS[a]
        if self.any_fruit:
            syms, pay = self.any_fruit
            if a in syms and b in syms and c in syms:
                return pay * bet, 'any three of ' + '/'.join(SYMBOLS[s] for s in sorted(syms))
        n = (a == CHERRY) + (b == CHERRY) + (c == CHERRY)
        pay = self.cherries.get(n)
        if pay:
            return pay * bet, '%d cherr%s' % (n, 'y' if n == 1 else 'ies')
        return 0, None

    def top_prize(self):
        """(symbol, pay) of the jackpot line."""
        s = max(self.three, key=lambda k: self.three[k])
        return s, self.three[s]


class Reels:
    def __init__(self, strips, paytable, rng):
        self.strips = strips
        self.paytable = paytable
        self.rng = rng
        self.stops = [0] * len(strips)

    def spin(self, bet):
        """Pick a stop on every reel. Returns (win, label); self.stops holds the result."""
        for i in range(len(self.strips)):
            self.stops[i] = self.rng.randrange(len(self.strips[i]))
        return self.paytable.evaluate(self.line(), bet)

    def line(self):
        return [self.strips[i][self.stops[i]] for i in range(len(self.strips))]

    def symbol_at(self, reel, offset):
        """Symbol `offset` stops after the current stop on `reel` (negative = before): for scrolling."""
        s = self.strips[reel]
        return s[(self.stops[reel] + offset) % len(s)]


def exact_stats(strips, paytable):
    """Enumerate every stop combination (equally likely). Returns a dict with rtp (fraction of the
    bet returned), hit (fraction of spins that pay), sd (standard deviation of the return per spin,
    in bets), top (probability of the top prize), and pays {label: (probability, pay)}."""
    import itertools
    total = 1
    for s in strips:
        total *= len(s)
    ret = 0.0
    ret2 = 0.0
    hits = 0
    pays = {}
    top_sym, top_pay = paytable.top_prize()
    top = 0
    for combo in itertools.product(*strips):
        win, label = paytable.evaluate(combo, 1)
        if win:
            hits += 1
            ret += win
            ret2 += win * win
            p, _ = pays.get(label, (0, win))
            pays[label] = (p + 1, win)
            if label == 'three ' + SYMBOLS[top_sym]:
                top += 1
    mean = ret / total
    var = ret2 / total - mean * mean
    return {
        'combos': total,
        'rtp': mean,
        'hit': hits / float(total),
        'sd': var ** 0.5,
        'top': top / float(total),
        'pays': {k: (v[0] / float(total), v[1]) for k, v in pays.items()},
    }
