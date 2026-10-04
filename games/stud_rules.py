# Caribbean Stud rules engine. Pure logic: no `machine` import, runs under CPython and MicroPython.
#
# Ruling DR-025: ante; five cards each from one shuffled deck; the dealer shows one card; the player
# folds (loses the ante) or raises exactly twice the ante; the dealer qualifies with ace-king or
# better; a non-qualifying dealer pays the ante 1:1 and returns the raise; a qualifying dealer who
# loses pays the ante 1:1 and the raise by RAISE_PAY; a qualifying dealer who wins takes both; ties
# push. No progressive. Everything is a parameter on Rules. Money is whole chips; the caller owns
# the bankroll, Round only reports the net change.

from cards import Shoe
from poker import (evaluate5, rank_value, name as hand_name, HIGH_CARD, PAIR, TWO_PAIR, TRIPS, STRAIGHT,
                   FLUSH, FULL_HOUSE, QUADS, STRAIGHT_FLUSH, ROYAL_FLUSH)

RAISE_PAY = {HIGH_CARD: 1, PAIR: 1, TWO_PAIR: 2, TRIPS: 3, STRAIGHT: 4, FLUSH: 5, FULL_HOUSE: 7,
             QUADS: 20, STRAIGHT_FLUSH: 50, ROYAL_FLUSH: 100}

FOLD = 'fold'            # player folded: -ante
NOQUALIFY = 'noqualify'  # dealer below A-K: +ante, raise returned
WIN = 'win'              # +ante + raise x pay
LOSE = 'lose'            # -ante - raise
PUSH = 'push'            # tie: 0

DECISION = 'decision'    # waiting for raise or fold
DONE = 'done'


class Rules:
    def __init__(self, raise_mult=2, raise_pay=RAISE_PAY, qualify_rank=13):
        self.raise_mult = raise_mult          # raise = ante x raise_mult
        self.raise_pay = raise_pay
        self.qualify_rank = qualify_rank      # dealer's second card must be at least this with an ace (13 = king)


def qualifies(value, rules=None):
    """A-K high card or better (DR-025)."""
    if value[0] > HIGH_CARD:
        return True
    q = rules.qualify_rank if rules else 13
    return value[1] == 14 and value[2] >= q


def is_ace_king(value):
    return value[0] == HIGH_CARD and value[1] == 14 and value[2] == 13


def advice(player, value, up):
    """Published basic strategy (Wizard of Odds): True = raise, False = fold. For the strategy
    screen and for the simulator; the game never decides for the player."""
    if value[0] > HIGH_CARD:
        return True
    if not is_ace_king(value):
        return False
    ranks = sorted([rank_value(c) for c in player], reverse=True)
    u = rank_value(up)
    if 2 <= u <= 12 and u in ranks:
        return True
    if u >= 13 and (12 in ranks or 11 in ranks):
        return True
    if u not in ranks and 12 in ranks and u < ranks[3]:
        return True
    return False


def describe(value):
    """'pair of 9s', 'ace-king', 'two pair', 'flush', ... for the hand-name lines."""
    cat = value[0]
    if cat == HIGH_CARD:
        if is_ace_king(value):
            return 'ace-king'
        return rank_word(value[1]) + ' high'
    if cat == PAIR:
        return 'pair of ' + rank_word(value[1]) + 's'
    if cat == TRIPS:
        return 'three ' + rank_word(value[1]) + 's'
    if cat == QUADS:
        return 'four ' + rank_word(value[1]) + 's'
    return hand_name(value)


def rank_word(v):
    return {14: 'ace', 13: 'king', 12: 'queen', 11: 'jack'}.get(v, str(v))


class Round:
    def __init__(self, shoe, rules, ante):
        self.shoe = shoe
        self.rules = rules
        self.ante = ante
        self.raise_bet = 0
        self.player = []
        self.dealer = []
        self.pv = None
        self.dv = None
        self.state = DECISION
        self.outcome = None
        self.net = 0

    def deal(self):
        s = self.shoe
        for _ in range(5):
            self.player.append(s.draw())
            self.dealer.append(s.draw())
        self.pv = evaluate5(self.player)
        self.dv = evaluate5(self.dealer)
        return self

    def up_card(self):
        return self.dealer[0]

    def stake(self):
        return self.ante + self.raise_bet

    def fold(self):
        self._need_decision()
        self._finish(FOLD, -self.ante)
        return self

    def raise_(self):
        """Raise exactly raise_mult x ante and show down. Caller checks the bankroll."""
        self._need_decision()
        r = self.ante * self.rules.raise_mult
        self.raise_bet = r
        if not qualifies(self.dv, self.rules):
            self._finish(NOQUALIFY, self.ante)
        elif self.pv > self.dv:
            self._finish(WIN, self.ante + r * self.rules.raise_pay[self.pv[0]])
        elif self.pv < self.dv:
            self._finish(LOSE, -(self.ante + r))
        else:
            self._finish(PUSH, 0)
        return self

    def dealer_qualifies(self):
        return qualifies(self.dv, self.rules)

    def _need_decision(self):
        if self.state != DECISION:
            raise ValueError('round is over')

    def _finish(self, outcome, net):
        self.state = DONE
        self.outcome = outcome
        self.net = net


def new_deck(rng):
    """One 52-card deck, reshuffled before every hand (Shoe with penetration 0 forces that)."""
    return Shoe(1, rng, penetration=0.0)
