"""Monte Carlo house-edge estimate for the blackjack rules engine (Mac/CPython only).

Plays a no-split basic strategy (hit / stand / double) for N hands per rule set and prints the
player's expected return as a percent of the amount bet (negative = house edge).
Run:  python3 tools/bj_edge.py [hands]
"""
import os
import random
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import tests.context  # noqa: E402,F401
from cards import hand_value  # noqa: E402
from blackjack_rules import Rules, Round, PLAYER  # noqa: E402


def action(r, up):
    """Return 'H', 'S' or 'D' (double if allowed, else hit/stand per fallback)."""
    total, soft = hand_value(r.player)
    can_dbl = r.can_double()
    h17 = r.rules.hit_soft_17
    if soft:
        if total >= 20:
            return 'S'
        if total == 19:
            return 'S'
        if total == 18:
            if up in (3, 4, 5, 6) and can_dbl:
                return 'D'
            return 'S' if up in (2, 7, 8) else 'H'
        if total == 17:
            return 'D' if (up in (3, 4, 5, 6) and can_dbl) else 'H'
        if total in (15, 16):
            return 'D' if (up in (4, 5, 6) and can_dbl) else 'H'
        return 'D' if (up in (5, 6) and can_dbl) else 'H'
    if total >= 17:
        return 'S'
    if total >= 13:
        return 'S' if up <= 6 else 'H'
    if total == 12:
        return 'S' if up in (4, 5, 6) else 'H'
    if total == 11:
        if can_dbl and (up != 11 or h17):
            return 'D'
        return 'H'
    if total == 10:
        return 'D' if (can_dbl and up <= 9) else 'H'
    if total == 9:
        return 'D' if (can_dbl and up in (3, 4, 5, 6)) else 'H'
    return 'H'


def run(args):
    decks, h17, num, den, hands, seed = args
    rules = Rules(decks=decks, hit_soft_17=h17, bj_num=num, bj_den=den)
    rng = random.Random(seed)
    shoe = rules.new_shoe(rng)
    staked = 0
    net = 0
    for _ in range(hands):
        if shoe.needs_shuffle():
            shoe.shuffle()
        r = Round(shoe, rules, 100).deal()
        up = hand_value([r.dealer[0]])[0]
        if r.dealer[0] % 13 == 0:
            up = 11
        while r.state == PLAYER:
            a = action(r, up)
            if a == 'S':
                r.stand()
            elif a == 'D':
                r.double()
            else:
                r.hit()
        staked += 100
        net += r.net
    return (decks, h17, num, den, 100.0 * net / staked)


if __name__ == '__main__':
    hands = int(sys.argv[1]) if len(sys.argv) > 1 else 2000000
    configs = []
    for decks in (1, 2, 6):
        for h17 in (False, True):
            for num, den in ((3, 2), (6, 5)):
                configs.append((decks, h17, num, den, hands, 1000 + len(configs)))
    with Pool() as p:
        for decks, h17, num, den, ev in p.imap(run, configs):
            print('%d deck%s  %s  BJ %d:%d   player return %+.2f%%' % (
                decks, 's' if decks > 1 else ' ', 'H17' if h17 else 'S17', num, den, ev))
