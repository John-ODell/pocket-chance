"""Monte Carlo house edge for Ultimate Texas Hold'em on lib/poker.py (for the Hold'em requests).

Rules (Wizard of Odds, wizardofodds.com/games/ultimate-texas-hold-em/): equal Ante and Blind; two
hole cards each; the player may raise 4x (or 3x) the Ante before the flop, else check; after the
flop a checked player may raise 2x; after the river a twice-checked player raises 1x or folds (losing
Ante and Blind). Showdown with the dealer's best five of seven. Dealer qualifies with a pair or
better; if not, the Ante pushes. Player wins: Ante (if dealer qualifies) and Play pay 1:1, Blind pays
by the table below for a straight or better and pushes otherwise. Player loses: all three lost.
Tie: all push. Reference: 2.185% of the Ante with optimal play; the Wizard's simple strategy 2.43%.

The strategy here is the Wizard's simple strategy WITHOUT the river "fewer than 21 dealer outs"
rule (which needs a 990-combination count per hand): river decision = raise 1x with a hidden pair
or better, else fold. That is a strategy a casual player can actually follow and is what the game's
help screen will show. Run:  python3 tools/uth_edge.py [hands]
"""
import os
import random
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import tests.context  # noqa: E402,F401
from poker import evaluate, evaluate5, rank_value, PAIR, STRAIGHT, FLUSH, FULL_HOUSE, QUADS, STRAIGHT_FLUSH, ROYAL_FLUSH, HIGH_CARD  # noqa: E402

BLIND_PAY = {STRAIGHT: (1, 1), FLUSH: (3, 2), FULL_HOUSE: (3, 1), QUADS: (10, 1), STRAIGHT_FLUSH: (50, 1), ROYAL_FLUSH: (500, 1)}


def suited(a, b):
    return a // 13 == b // 13


def preflop_raise(hole):
    """Wizard simple strategy, large raise: any pair but 2s; any ace; K-2s+ / K-5o+; Q-6s+ / Q-8o+;
    J-8s+ / J-10o."""
    a, b = sorted([rank_value(c) for c in hole], reverse=True)
    s = suited(hole[0], hole[1])
    if a == b:
        return a >= 3
    if a == 14:
        return True
    if a == 13:
        return b >= 2 if s else b >= 5
    if a == 12:
        return b >= 6 if s else b >= 8
    if a == 11:
        return b >= 8 if s else b >= 10
    return False


def hidden_pair_or_better(hole, board):
    """Best hand uses at least one hole card and is a pair or better (a pair on the board alone
    does not count)."""
    v = evaluate(hole + board)
    if v[0] < PAIR:
        return False
    bv = evaluate5(board) if len(board) == 5 else (evaluate(board) if len(board) >= 5 else None)
    if len(board) == 3:
        # with three board cards a pair must involve a hole card unless the board itself pairs
        board_pair = len(set(c % 13 for c in board)) < 3
        if v[0] == PAIR and board_pair:
            return False
        return True
    return v > bv


def flop_raise(hole, board):
    """Medium raise: two pair or better, hidden pair (except pocket 2s), or four to a flush with a
    hidden ten or better."""
    v = evaluate(hole + board)
    if v[0] >= 2:
        return True
    if hidden_pair_or_better(hole, board):
        if not (hole[0] % 13 == hole[1] % 13 and rank_value(hole[0]) == 2):
            return True
    cards = hole + board
    for suit in range(4):
        same = [c for c in cards if c // 13 == suit]
        if len(same) >= 4 and any(c in hole and rank_value(c) >= 10 for c in same):
            return True
    return False


def play(deck, rng, four_x=True):
    rng.shuffle(deck)
    hole = deck[:2]
    dealer = deck[2:4]
    board = deck[4:9]
    ante = 1
    if preflop_raise(hole):
        play_bet = 4 if four_x else 3
    elif flop_raise(hole, board[:3]):
        play_bet = 2
    elif hidden_pair_or_better(hole, board):
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
    label, four_x, hands, seed = args
    rng = random.Random(seed)
    deck = list(range(52))
    net = 0.0
    staked = 0
    folds = 0
    for _ in range(hands):
        n, s = play(deck, rng, four_x)
        net += n
        staked += s
        if s == 2:
            folds += 1
    return label, 100.0 * net / hands, 100.0 * net / staked, 100.0 * folds / hands


if __name__ == '__main__':
    hands = int(sys.argv[1]) if len(sys.argv) > 1 else 400000
    configs = [('simple strategy, 4x pre-flop raise', True), ('simple strategy, 3x pre-flop raise', False)]
    with Pool() as p:
        for label, per_ante, per_staked, folds in p.imap(run, [(l, f, hands, 900 + i) for i, (l, f) in enumerate(configs)]):
            print('%-40s house edge %.2f%% of the ante  (%.2f%% of all chips staked)  folds %.1f%%'
                  % (label, -per_ante, -per_staked, folds))
