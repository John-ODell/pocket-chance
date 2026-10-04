"""House edge for punto banco baccarat (for the baccarat decision requests).

Rules (Wizard of Odds, wizardofodds.com/games/baccarat/): eight decks; aces count 1, tens and faces 0,
totals modulo 10. Two cards each. A natural 8 or 9 on either side ends the hand. Otherwise the
Player draws on 0-5 and stands on 6-7; the Banker draws on 0-5 and stands on 6-7 when the Player
stood, and when the Player drew a third card of value v: draws on 0-2, on 3 unless v is 8, on 4 when
v is 2-7, on 5 when v is 4-7, on 6 when v is 6-7, stands on 7. Higher total wins, equal totals tie.
Pays: Player 1:1; Banker 1:1 less 5% commission (or the "no commission" variant: a Banker win with a
total of 6 pays 1:2); Tie 8:1 (or 9:1); a tie pushes the Player and Banker bets.
Published (8 decks): Banker 1.06%, Player 1.24%, Tie 8:1 14.36%, Tie 9:1 4.84%, no-commission
Banker 1.46%.

Two methods: an exact enumeration over card values drawn without replacement from a full
eight-deck shoe, and a Monte Carlo run on lib/cards.Shoe with a cut card, as the game will play.
Run:  python3 tools/baccarat_edge.py [hands]
"""
import os
import random
import sys
from fractions import Fraction
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import tests.context  # noqa: E402,F401
from cards import Shoe  # noqa: E402

DECKS = 8
CUT_CARD = 14                     # cards left when the cut card is reached (the hand in play finishes)


def points(card):
    r = card % 13
    return 0 if r >= 9 else r + 1


def banker_draws(b, player_third):
    """Third-card rule for the Banker. `player_third` is the Player's third card value or None."""
    if player_third is None:
        return b <= 5
    v = player_third
    if b <= 2:
        return True
    if b == 3:
        return v != 8
    if b == 4:
        return 2 <= v <= 7
    if b == 5:
        return 4 <= v <= 7
    if b == 6:
        return v in (6, 7)
    return False


def settle(p, b, banker_pay, tie_pay):
    """(net on 1 unit Player, net on 1 unit Banker, net on 1 unit Tie)."""
    if p == b:
        return 0, 0, tie_pay
    if p > b:
        return 1, -1, -1
    return -1, banker_pay(b), -1


def commission(b):
    return Fraction(95, 100)


def no_commission(b):
    return Fraction(1, 2) if b == 6 else Fraction(1)


# ---- exact enumeration ---------------------------------------------------------------------------
def exact():
    """Expected value per unit for Player, Banker (5%), Banker (no commission), Tie 8:1, Tie 9:1,
    enumerating card values without replacement from a full shoe."""
    counts0 = [32 * DECKS // 8 * 4] + [32 * DECKS // 8] * 9     # value 0: 128 cards, 1-9: 32 each
    total = sum(counts0)
    ev = [Fraction(0)] * 5
    nat = Fraction(0)

    def draw(counts, remaining):
        """Values still in the shoe with their draw probability; the caller takes the card out."""
        for v in range(10):
            if counts[v]:
                yield v, Fraction(counts[v], remaining)

    counts = list(counts0)
    for p1, w1 in draw(counts, total):
        counts[p1] -= 1
        for b1, w2 in draw(counts, total - 1):
            counts[b1] -= 1
            for p2, w3 in draw(counts, total - 2):
                counts[p2] -= 1
                for b2, w4 in draw(counts, total - 3):
                    counts[b2] -= 1
                    w = w1 * w2 * w3 * w4
                    p = (p1 + p2) % 10
                    b = (b1 + b2) % 10
                    if p >= 8 or b >= 8:
                        nat += w
                        _accumulate(ev, p, b, w)
                    else:
                        _third_cards(ev, counts, total - 4, p, b, w)
                    counts[b2] += 1
                counts[p2] += 1
            counts[b1] += 1
        counts[p1] += 1
    return ev, nat


def _third_cards(ev, counts, remaining, p, b, w):
    if p <= 5:
        for v in range(10):
            if counts[v]:
                wp = w * Fraction(counts[v], remaining)
                counts[v] -= 1
                np = (p + v) % 10
                if banker_draws(b, v):
                    for u in range(10):
                        if counts[u]:
                            wb = wp * Fraction(counts[u], remaining - 1)
                            _accumulate(ev, np, (b + u) % 10, wb)
                else:
                    _accumulate(ev, np, b, wp)
                counts[v] += 1
    else:
        if banker_draws(b, None):
            for u in range(10):
                if counts[u]:
                    wb = w * Fraction(counts[u], remaining)
                    _accumulate(ev, p, (b + u) % 10, wb)
        else:
            _accumulate(ev, p, b, w)


def _accumulate(ev, p, b, w):
    pl, bk, tie8 = settle(p, b, commission, 8)
    _, bk_nc, tie9 = settle(p, b, no_commission, 9)
    ev[0] += w * pl
    ev[1] += w * bk
    ev[2] += w * bk_nc
    ev[3] += w * tie8
    ev[4] += w * tie9


# ---- Monte Carlo on the real Shoe ----------------------------------------------------------------
def play(shoe):
    """One coup on the shoe. Returns (player total, banker total, cards used)."""
    p1, b1, p2, b2 = shoe.draw(), shoe.draw(), shoe.draw(), shoe.draw()
    p = (points(p1) + points(p2)) % 10
    b = (points(b1) + points(b2)) % 10
    used = 4
    if p >= 8 or b >= 8:
        return p, b, used
    third = None
    if p <= 5:
        third = points(shoe.draw())
        p = (p + third) % 10
        used += 1
    if banker_draws(b, third):
        b = (b + points(shoe.draw())) % 10
        used += 1
    return p, b, used


def run(args):
    hands, seed = args
    rng = random.Random(seed)
    shoe = Shoe(DECKS, rng, penetration=1.0 - CUT_CARD / (52.0 * DECKS))
    net = [0.0] * 5
    shuffles = 0
    for _ in range(hands):
        if shoe.needs_shuffle():
            shoe.shuffle()
            shuffles += 1
        p, b, _ = play(shoe)
        pl, bk, tie8 = settle(p, b, commission, 8)
        _, bk_nc, tie9 = settle(p, b, no_commission, 9)
        for i, v in enumerate((pl, bk, bk_nc, tie8, tie9)):
            net[i] += float(v)
    return net, shuffles


LABELS = ('Player 1:1', 'Banker 1:1 less 5%', 'Banker no commission (6 pays 1:2)', 'Tie 8:1', 'Tie 9:1')
PUBLISHED = (1.24, 1.06, 1.46, 14.36, 4.84)

if __name__ == '__main__':
    hands = int(sys.argv[1]) if len(sys.argv) > 1 else 1000000
    ev, nat = exact()
    print('Exact, full eight-deck shoe (naturals end %.1f%% of coups):' % (100 * float(nat)))
    for label, e, pub in zip(LABELS, ev, PUBLISHED):
        print('  %-36s house edge %.3f%%   (published %.2f%%)' % (label, -100 * float(e), pub))
    jobs = [(hands, 900 + i) for i in range(8)]
    with Pool() as pool:
        results = pool.map(run, jobs)
    total = [sum(r[0][i] for r in results) for i in range(5)]
    n = hands * len(jobs)
    print('Monte Carlo on lib/cards.Shoe, %d coups, cut card at %d cards, %d shuffles:'
          % (n, CUT_CARD, sum(r[1] for r in results)))
    for label, t in zip(LABELS, total):
        print('  %-36s house edge %.3f%%' % (label, -100 * t / n))
