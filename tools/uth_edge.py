"""Monte Carlo house edge for Ultimate Texas Hold'em on lib/poker.py (for the Hold'em requests).

Rules (Wizard of Odds, wizardofodds.com/games/ultimate-texas-hold-em/): equal Ante and Blind; two
hole cards each; the player may raise 4x (or 3x) the Ante before the flop, else check; after the
flop a checked player may raise 2x; after the river a twice-checked player raises 1x or folds (losing
Ante and Blind). Showdown with the dealer's best five of seven. Dealer qualifies with a pair or
better; if not, the Ante pushes. Player wins: Ante (if dealer qualifies) and Play pay 1:1, Blind pays
by the table below for a straight or better and pushes otherwise. Player loses: all three lost.
Tie: all push. Reference: 2.185% of the Ante with optimal play; the Wizard's simple strategy 2.43%.

Two strategies are measured: the Wizard's simple strategy in full (river: raise 1x with a hidden
pair or better, or when fewer than 21 of the 45 unseen cards would give the dealer a better hand
than yours; else fold), and the same without the outs count (river: hidden pair or better, else
fold), which is what a player can follow with no help from the device.
Run:  python3 tools/uth_edge.py [hands]
"""
import os
import random
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import tests.context  # noqa: E402,F401
from poker import evaluate, PAIR  # noqa: E402
from holdem_rules import (BLIND_PAY, preflop_raise, flop_raise, hidden_pair_or_better,  # noqa: E402,F401
                          dealer_outs, river_raise)


def play(deck, rng, four_x=True, use_outs=False):
    rng.shuffle(deck)
    hole = deck[:2]
    dealer = deck[2:4]
    board = deck[4:9]
    ante = 1
    if preflop_raise(hole):
        play_bet = 4 if four_x else 3
    elif flop_raise(hole, board[:3]):
        play_bet = 2
    elif river_raise(hole, board, dealer_outs(hole, board) if use_outs else None):
        play_bet = 1
    else:
        return -2, 2                                  # fold: lose Ante and Blind
    pv = evaluate(hole + board)
    dv = evaluate(dealer + board)
    staked = 2 + play_bet
    if pv > dv:
        net = play_bet
        if dv[0] >= PAIR:
            net += ante
        if pv[0] in BLIND_PAY:
            n, d = BLIND_PAY[pv[0]]
            net += ante * n // d if d == 1 else (ante * n) / d
        return net, staked
    if pv < dv:
        return -(play_bet + 1 + (1 if dv[0] >= PAIR else 0)), staked
    return 0, staked


def run(args):
    label, four_x, use_outs, hands, seed = args
    rng = random.Random(seed)
    deck = list(range(52))
    net = 0.0
    staked = 0
    folds = 0
    for _ in range(hands):
        n, s = play(deck, rng, four_x, use_outs)
        net += n
        staked += s
        if s == 2:
            folds += 1
    return label, 100.0 * net / hands, 100.0 * net / staked, 100.0 * folds / hands


if __name__ == '__main__':
    hands = int(sys.argv[1]) if len(sys.argv) > 1 else 200000
    configs = [('Wizard simple strategy (with river outs)', True, True),
               ('simple strategy without the outs count', True, False),
               ('without outs, 3x pre-flop raise', False, False)]
    # split each config over several seeds so all cores work
    jobs = []
    for i, (l, f, o) in enumerate(configs):
        for k in range(8):
            jobs.append((l, f, o, hands // 8, 900 + 10 * i + k))
    with Pool() as p:
        results = {}
        for label, per_ante, per_staked, folds in p.imap(run, jobs):
            results.setdefault(label, []).append((per_ante, per_staked, folds))
        for label, _, _ in configs:
            rs = results[label]
            per_ante = sum(r[0] for r in rs) / len(rs)
            per_staked = sum(r[1] for r in rs) / len(rs)
            folds = sum(r[2] for r in rs) / len(rs)
            print('%-40s house edge %.2f%% of the ante  (%.2f%% of all chips staked)  folds %.1f%%'
                  % (label, -per_ante, -per_staked, folds))
