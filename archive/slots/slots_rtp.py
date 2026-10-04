"""Exact RTP, hit frequency and volatility for candidate slots configurations (DR-017, DR-018).

Every stop combination is enumerated (32^3 = 32,768 for 32-stop reels), so the numbers are exact,
not sampled. Run:  python3 tools/slots_rtp.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import tests.context  # noqa: E402,F401
from slots_rules import (strip, Paytable, exact_stats, SYMBOLS,  # noqa: E402
                         CHERRY, LEMON, ORANGE, BELL, BAR, SEVEN, DIAMOND, STAR)

# Strip used by every candidate: 32 stops per reel, identical reels. Cherry is the "small win"
# symbol, so its count sets the hit frequency; star is the jackpot symbol with one stop per reel.
COUNTS = {CHERRY: 3, LEMON: 7, ORANGE: 6, BELL: 5, BAR: 4, SEVEN: 3, DIAMOND: 3, STAR: 1}
THREE = {STAR: 1000, DIAMOND: 200, SEVEN: 100, BAR: 40, BELL: 20, ORANGE: 14, LEMON: 10, CHERRY: 8}

PAY_A = Paytable(three=THREE, cherries={2: 3, 1: 1})                       # recommended
PAY_B = Paytable(three=THREE, cherries={2: 4, 1: 1})                       # more generous
PAY_C = Paytable(three={**THREE, STAR: 2000}, cherries={2: 2, 1: 1})       # bigger jackpot, more volatile

CANDIDATES = (('A  one cherry pays 1, two pay 3, three stars 1000', COUNTS, PAY_A),
              ('B  as A but two cherries pay 4', COUNTS, PAY_B),
              ('C  as A but two cherries pay 2 and three stars pay 2000', COUNTS, PAY_C))


def report(label, counts, pay):
    strips = [strip(counts)] * 3
    st = exact_stats(strips, pay)
    print('%s' % label)
    print('  stops/reel %d, combos %d' % (len(strips[0]), st['combos']))
    print('  RTP %.2f%%   house edge %.2f%%   hit frequency 1 in %.1f (%.1f%%)   SD %.1f bets' % (
        100 * st['rtp'], 100 * (1 - st['rtp']), 1 / st['hit'], 100 * st['hit'], st['sd']))
    print('  top prize 1 in %d spins' % round(1 / st['top']))
    for k, (p, w) in sorted(st['pays'].items(), key=lambda kv: -kv[1][1]):
        print('    %-32s pays %5d   1 in %8.1f   contributes %5.2f%% RTP' % (k, w, 1 / p, 100 * p * w))
    return st


if __name__ == '__main__':
    for label, counts, pay in CANDIDATES:
        report(label, counts, pay)
        print()
