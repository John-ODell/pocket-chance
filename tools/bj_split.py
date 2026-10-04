"""Monte Carlo: what pair splitting does to the house edge (for decision request DR-016).

Simulates hands directly on the Shoe (the engine has no split yet), with the no-split basic
strategy from bj_edge.py plus the usual pair-splitting table. Options match DR-016's choices.
Run:  python3 tools/bj_split.py [hands]        (Mac only, CPython)
"""
import os
import random
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import tests.context  # noqa: E402,F401
from cards import hand_value, card_points, Shoe  # noqa: E402
from blackjack_rules import Rules, dealer_should_hit  # noqa: E402
from bj_edge import action  # noqa: E402


class Opts:
    def __init__(self, split=False, max_hands=2, das=True, split_aces=True, resplit_aces=False):
        self.split = split            # pairs may be split at all
        self.max_hands = max_hands    # 2 = split once, 4 = re-split up to four hands
        self.das = das                # double after split allowed
        self.split_aces = split_aces  # aces may be split (one card each, then stand)
        self.resplit_aces = resplit_aces


def should_split(pair_rank, up, opts):
    """Basic strategy for pairs (6 decks, S17). pair_rank: 1 = ace, 10 = ten-value."""
    if pair_rank == 1:
        return opts.split_aces
    if pair_rank == 8:
        return True
    if pair_rank in (2, 3, 7):
        return up <= 7
    if pair_rank == 6:
        return up <= 6
    if pair_rank == 9:
        return up in (2, 3, 4, 5, 6, 8, 9)
    if pair_rank == 4:
        return opts.das and up in (5, 6)
    return False     # 5,5 and T,T never


class Hand:
    def __init__(self, cards, bet):
        self.cards = cards
        self.bet = bet
        self.split_aces = False


class Fake:
    """Minimal stand-in for Round so bj_edge.action() can be reused on a split hand."""
    def __init__(self, cards, rules, can_dbl):
        self.player = cards
        self.rules = rules
        self._can = can_dbl

    def can_double(self):
        return self._can


def play_hand(shoe, rules, opts, bet=100):
    p = [shoe.draw(), shoe.draw()]
    d = [shoe.draw(), shoe.draw()]
    up = card_points(d[0])
    if d[0] % 13 == 0:
        up = 11
    p_bj = hand_value(p)[0] == 21
    d_bj = hand_value(d)[0] == 21
    if p_bj or d_bj:
        if p_bj and d_bj:
            return 0, bet
        if p_bj:
            return bet * rules.bj_num // rules.bj_den, bet
        return -bet, bet
    hands = [Hand(p, bet)]
    staked = bet
    # splitting
    i = 0
    while i < len(hands):
        hd = hands[i]
        c = hd.cards
        if (opts.split and len(c) == 2 and len(hands) < opts.max_hands
                and card_points(c[0]) == card_points(c[1]) and (c[0] % 13) == (c[1] % 13)
                and should_split(card_points(c[0]), up, opts)
                and not (hd.split_aces and not opts.resplit_aces)):
            new = Hand([c[1], shoe.draw()], bet)
            hd.cards = [c[0], shoe.draw()]
            staked += bet
            if card_points(c[0]) == 1:
                hd.split_aces = new.split_aces = True
            hands.insert(i + 1, new)
            continue        # re-examine this hand (it may be a pair again)
        i += 1
    # play each hand
    for hd in hands:
        if hd.split_aces:
            continue        # one card each, stand
        while True:
            total = hand_value(hd.cards)[0]
            if total >= 21:
                break
            can_dbl = len(hd.cards) == 2 and (len(hands) == 1 or opts.das)
            a = action(Fake(hd.cards, rules, can_dbl), up)
            if a == 'S':
                break
            hd.cards.append(shoe.draw())
            if a == 'D':
                hd.bet *= 2
                staked += bet
                break
    # dealer
    if any(hand_value(hd.cards)[0] <= 21 for hd in hands):
        while dealer_should_hit(d, rules.hit_soft_17):
            d.append(shoe.draw())
    dt = hand_value(d)[0]
    net = 0
    for hd in hands:
        pt = hand_value(hd.cards)[0]
        if pt > 21:
            net -= hd.bet
        elif dt > 21 or pt > dt:
            net += hd.bet
        elif pt < dt:
            net -= hd.bet
    return net, staked


def run(args):
    label, opts, hands, seed = args
    rules = Rules()
    rng = random.Random(seed)
    shoe = rules.new_shoe(rng)
    net = 0
    staked = 0
    initial = 0
    for _ in range(hands):
        if shoe.needs_shuffle():
            shoe.shuffle()
        n, s = play_hand(shoe, rules, opts)
        net += n
        staked += s
        initial += 100
    return label, 100.0 * net / initial, 100.0 * net / staked


if __name__ == '__main__':
    hands = int(sys.argv[1]) if len(sys.argv) > 1 else 2000000
    configs = [
        ('A  no split (v1 as shipped)', Opts(split=False)),
        ('B  split once, any pair, aces one card, double after split', Opts(split=True, max_hands=2, das=True)),
        ('B2 split once, no double after split', Opts(split=True, max_hands=2, das=False)),
        ('B3 split once, no aces', Opts(split=True, max_hands=2, das=True, split_aces=False)),
        ('C  re-split to 4 hands, double after split, no re-split aces', Opts(split=True, max_hands=4, das=True)),
    ]
    with Pool() as p:
        for label, ev_init, ev_staked in p.imap(run, [(l, o, hands, 500 + i) for i, (l, o) in enumerate(configs)]):
            print('%-62s player return %+.2f%% of initial bet  (%+.2f%% of all chips staked)' % (label, ev_init, ev_staked))
