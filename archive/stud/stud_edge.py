"""Monte Carlo house edge for Caribbean Stud on lib/poker.py (for the Caribbean Stud requests).

Rules (Wizard of Odds, wizardofodds.com/games/caribbean-stud-poker/): ante; 5 cards each, one dealer
card up; fold (lose the ante) or raise exactly 2x ante; dealer qualifies with A-K or better; a
non-qualifying dealer pays the ante 1:1 and pushes the raise; a qualifying dealer who loses pays the
ante 1:1 and the raise by the table (pair or less 1, two pair 2, trips 3, straight 4, flush 5, full
house 7, quads 20, straight flush 50, royal 100); a qualifying dealer who wins takes both; ties push.
Reference: house edge 5.224% of the ante with optimal play.
Run:  python3 tools/stud_edge.py [hands]
"""
import os
import random
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import tests.context  # noqa: E402,F401
from poker import evaluate5, rank_value, HIGH_CARD, PAIR, TWO_PAIR, TRIPS, STRAIGHT, FLUSH, FULL_HOUSE, QUADS, STRAIGHT_FLUSH, ROYAL_FLUSH  # noqa: E402

RAISE_PAY = {HIGH_CARD: 1, PAIR: 1, TWO_PAIR: 2, TRIPS: 3, STRAIGHT: 4, FLUSH: 5, FULL_HOUSE: 7,
             QUADS: 20, STRAIGHT_FLUSH: 50, ROYAL_FLUSH: 100}


def qualifies(value):
    """Dealer qualifies with A-K high card or better."""
    if value[0] > HIGH_CARD:
        return True
    return value[1] == 14 and value[2] == 13


def is_ak(value):
    return value[0] == HIGH_CARD and value[1] == 14 and value[2] == 13


def strategy_simple(player, value, up):
    """Raise with a pair or better, or A-K; fold below A-K."""
    return value[0] > HIGH_CARD or is_ak(value)


def strategy_wizard(player, value, up):
    """Wizard of Odds basic strategy. With A-K: raise if the dealer's up-card is 2-Q and matches one
    of yours; or the up-card is A or K and you have a Q or J; or the up-card matches none of yours and
    you have a Q and the up-card is lower than your fourth-highest card. Otherwise fold A-K."""
    if value[0] > HIGH_CARD:
        return True
    if not is_ak(value):
        return False
    ranks = sorted([rank_value(c) for c in player], reverse=True)    # 14, 13, x, y, z
    u = rank_value(up)
    if 2 <= u <= 12 and u in ranks:
        return True
    if u >= 13 and (12 in ranks or 11 in ranks):
        return True
    if u not in ranks and 12 in ranks and u < ranks[3]:
        return True
    return False


def play(deck, rng, strategy, ante=1):
    rng.shuffle(deck)
    player = deck[:5]
    dealer = deck[5:10]
    pv = evaluate5(player)
    dv = evaluate5(dealer)
    if not strategy(player, pv, dealer[0]):
        return -ante, ante
    raise_bet = 2 * ante
    staked = ante + raise_bet
    if not qualifies(dv):
        return ante, staked
    if pv > dv:
        return ante + raise_bet * RAISE_PAY[pv[0]], staked
    if pv < dv:
        return -staked, staked
    return 0, staked


def run(args):
    label, strategy, hands, seed = args
    rng = random.Random(seed)
    deck = list(range(52))
    net = 0
    staked = 0
    folds = 0
    for _ in range(hands):
        n, s = play(deck, rng, strategy)
        net += n
        staked += s
        if s == 1:
            folds += 1
    return label, 100.0 * net / hands, 100.0 * net / staked, 100.0 * folds / hands


if __name__ == '__main__':
    hands = int(sys.argv[1]) if len(sys.argv) > 1 else 2000000
    configs = [('raise with pair or A-K, fold below', strategy_simple),
               ('Wizard of Odds basic strategy', strategy_wizard)]
    with Pool() as p:
        for label, per_ante, per_staked, folds in p.imap(run, [(l, s, hands, 700 + i) for i, (l, s) in enumerate(configs)]):
            print('%-40s house edge %.2f%% of the ante  (%.2f%% of all chips staked)  folds %.1f%% of hands'
                  % (label, -per_ante, -per_staked, folds))
