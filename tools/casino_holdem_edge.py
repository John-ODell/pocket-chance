"""Monte Carlo house edge for John's Caribbean replacement: Casino Hold'em with a low or high call
and an optional WSOP-style table multiplier (for the DR-062 family).

Rules as John described them (2026-10-06) mapped onto Casino Hold'em (wizardofodds.com/games/
casino-holdem/): Ante; two cards to the player, two to the dealer, two to each AI seat; three
community cards turn; the player folds (losing the Ante), calls LOW (1x Ante) or HIGH (2x Ante);
the last two community cards turn; the dealer qualifies with a pair of fours or better. Dealer not
qualified: the Ante pays by the table and the call pushes. Dealer qualified and beaten: the Ante
pays by the table and the call 1:1. Dealer wins: Ante and call lost. Tie: push.
Ante table: royal flush 100, straight flush 20, four of a kind 10, full house 3, flush 2, else 1.
Published Casino Hold'em (call fixed at 2x): house edge 2.16% of the Ante with optimal play.

Multiplier (John's WSOP rule): when every player at the table (the player and the N-1 seats) beats
the dealer, the next hand pays winners N times. Two readings are measured: the multiplier on the
whole win (Ante table pay + call), or on the call bet only.

Run:  python3 tools/casino_holdem_edge.py [hands]
"""
import os
import random
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import tests.context  # noqa: E402,F401
from poker import evaluate, evaluate5, rank_value, HIGH_CARD, PAIR, TWO_PAIR, FLUSH, FULL_HOUSE, QUADS, STRAIGHT_FLUSH, ROYAL_FLUSH  # noqa: E402
import caribbean_rules  # noqa: E402

ANTE_PAY = {ROYAL_FLUSH: 100, STRAIGHT_FLUSH: 20, QUADS: 10, FULL_HOUSE: 3, FLUSH: 2}
FOLD, LOW, HIGH = 0, 1, 2


QUALIFY_PAIR = 4


def qualifies(dv):
    """Pair of fours or better (QUALIFY_PAIR sets the rank)."""
    if dv[0] > PAIR:
        return True
    return dv[0] == PAIR and dv[1] >= QUALIFY_PAIR


def has_draw(hole, flop):
    cards = hole + flop
    suits = [0] * 4
    for c in cards:
        suits[c // 13] += 1
    if max(suits) >= 4 and any(suits[c // 13] >= 4 for c in hole):
        return True
    ranks = set(rank_value(c) for c in cards)
    if 14 in ranks:
        ranks.add(1)
    hole_ranks = set(rank_value(c) for c in hole)
    for low in range(1, 11):
        run = [r for r in range(low, low + 5) if r in ranks]
        if len(run) >= 4 and hole_ranks & set(run) and low >= 2 and low + 4 <= 14:
            return True             # open-ended or gutshot four to a straight using a hole card
    return False


STRAT = 1


def decide(hole, flop, two_sizes=True):
    """Heuristic strategy. Returns FOLD, LOW or HIGH (HIGH only when two_sizes); the caller maps
    LOW and HIGH to call sizes."""
    if STRAT == 0:                                  # the game's taught strategy (caribbean_rules.advice)
        a = caribbean_rules.advice(hole, flop)
        return FOLD if a is None else (HIGH if (a == caribbean_rules.HIGH and two_sizes) else LOW)
    v = evaluate5(hole + flop)
    hole_ranks = [rank_value(c) for c in hole]
    board_ranks = [rank_value(c) for c in flop]
    big = HIGH if two_sizes else LOW
    if v[0] >= TWO_PAIR:
        return big
    if v[0] == PAIR:
        if v[1] in hole_ranks:
            return big                              # a pair using a hole card
        return LOW                                  # board pair, play along
    if has_draw(hole, flop):
        return big if STRAT != 3 else LOW
    if STRAT == 1:
        if max(hole_ranks) >= 13 or max(hole_ranks) > max(board_ranks):
            return LOW
    elif STRAT == 2:
        if max(hole_ranks) >= 14 or (max(hole_ranks) > max(board_ranks) and min(hole_ranks) > min(board_ranks)):
            return LOW
    elif STRAT == 3:
        if max(hole_ranks) > max(board_ranks):
            return LOW
    return FOLD


def deal(deck, rng, seats):
    rng.shuffle(deck)
    i = 0
    hands = []
    for _ in range(seats + 1):
        hands.append(deck[i:i + 2])
        i += 2
    dealer = deck[i:i + 2]
    i += 2
    board = deck[i:i + 5]
    return hands, dealer, board


def settle(hole, board, dv, ante, call, mult_all, mult_call, unq):
    """Net for one player. `call` is the call bet (0 = fold); `unq` is what the Ante does against an
    unqualified dealer: 'pay' by the table or 'push'. Returns (net, beat_dealer, beat_qualified, staked)."""
    if not call:
        return -ante, False, False, ante
    pv = evaluate(hole + board)
    staked = ante + call
    if not qualifies(dv):
        if unq == 'pay':
            win = ante * ANTE_PAY.get(pv[0], 1) * mult_all
        elif unq == 'even':
            win = ante * mult_all
        else:
            win = 0
        return win, True, False, staked
    if pv > dv:
        return ante * ANTE_PAY.get(pv[0], 1) * mult_all + call * mult_all * mult_call, True, True, staked
    if pv < dv:
        return -staked, False, False, staked
    return 0, False, False, staked


def run(args):
    global STRAT, QUALIFY_PAIR
    label, hands, seed, seats, sizes, unq, mult_mode, trigger, cap, STRAT, QUALIFY_PAIR = args
    rng = random.Random(seed)
    deck = list(range(52))
    net = staked = 0
    folds = triggers = 0
    armed = False
    n = min(seats + 1, cap)
    two_sizes = sizes[0] != sizes[1]
    for _ in range(hands):
        hs, dealer, board = deal(deck, rng, seats)
        dv = evaluate(dealer + board)
        flop = board[:3]
        if armed and mult_mode == 'all':
            m_all, m_call = n, 1
        elif armed and mult_mode == 'call':
            m_all, m_call = 1, n
        else:
            m_all, m_call = 1, 1
        all_beat = True
        for k, hole in enumerate(hs):
            action = decide(hole, flop, two_sizes)
            call = 0 if action == FOLD else sizes[action - 1]
            r, beat, beat_q, s = settle(hole, board, dv, 1, call, m_all, m_call, unq)
            if not (beat_q if trigger == 'qualified' else beat):
                all_beat = False
            if k == 0:
                net += r
                staked += s
                if action == FOLD:
                    folds += 1
        armed = mult_mode != 'none' and all_beat
        if armed:
            triggers += 1
    return label, 100.0 * net / hands, 100.0 * net / staked, 100.0 * folds / hands, 100.0 * triggers / hands


if __name__ == '__main__':
    hands = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
    # (label, seats, (low call, high call) in Antes, unqualified Ante, multiplier on, trigger, cap on N)
    # (label, seats, (low call, high call) in Antes, unqualified Ante, multiplier on, trigger, cap on N, strategy)
    S = 2
    # (label, seats, (low, high) in Antes, unqualified: 'pay' table / 'even' / 'push', multiplier on
    #  'none' / 'call' / 'all', trigger 'any' / 'qualified', cap on N, strategy (0 = the game's), qualifying pair)
    # (label, seats, (low, high) in Antes, unqualified: 'pay' table / 'even' / 'push', multiplier on
    #  'none' / 'call' / 'all', trigger 'any' / 'qualified', cap on N, strategy (0 = the game's), qualifying pair)
    configs = [
        ("Caribbean as built: 2x/4x, unq. push, x3 on the WHOLE win, qualified", 4, (2, 4), 'push', 'all', 'qualified', 3, 0, 4),
        ("  same with x2 on the whole win", 4, (2, 4), 'push', 'all', 'qualified', 2, 0, 4),
        ("  same with x3 on the call only (previous build)", 4, (2, 4), 'push', 'call', 'qualified', 3, 0, 4),
        ("  same with no multiplier", 4, (2, 4), 'push', 'none', 'any', 9, 0, 4),
        ("fixed 2x, Ante table vs unqualified (published game), game strategy", 4, (2, 2), 'pay', 'none', 'any', 9, 0, 4),
    ]
    jobs = []
    for i, cfg in enumerate(configs):
        for j in range(4):
            jobs.append((cfg[0], hands // 4, 1000 * i + j) + cfg[1:])
    with Pool() as p:
        results = p.map(run, jobs)
    for cfg in configs:
        label = cfg[0]
        rows = [r for r in results if r[0] == label]
        k = len(rows)
        print('%-60s edge %6.2f%% of Ante (%6.2f%% of staked)  folds %.1f%%  trigger %5.2f%%'
              % (label, -sum(r[1] for r in rows) / k, -sum(r[2] for r in rows) / k,
                 sum(r[3] for r in rows) / k, sum(r[4] for r in rows) / k))
