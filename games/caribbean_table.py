# Caribbean session: Ante limits against the shared bankroll (DR-068: 5 to 50, capped so Ante +
# high call is always covered), the hand flow with the seats (DR-069) and the armed multiplier
# (DR-064). Pure logic: no `machine` import.

from cards import Shoe
from caribbean_rules import Rules, Round, DECIDING, DONE, FOLD
from caribbean_seats import Seats

MIN_ANTE, MAX_ANTE, STEP = 5, 50, 5

BETTING = 'betting'
RESULT = 'result'
BROKE = 'broke'
# while a hand is in play the table's state is DECIDING (the flop is up)


class CaribbeanTable:
    def __init__(self, rng, bankroll, rules=None, seats=4):
        self.rules = rules or Rules()
        self.bankroll = bankroll
        self.shoe = Shoe(1, rng, penetration=0.0)        # a fresh deck every hand
        self.round = None
        self.seats = Seats(seats)
        self.armed = False                                # the NEXT hand's call wins mult_cap times
        self._fit_ante()
        self.state = BROKE if self.is_broke() else BETTING

    @property
    def exposure(self):
        return 1 + self.rules.high

    def is_broke(self):
        return self.bankroll.balance < MIN_ANTE * self.exposure

    def max_ante(self):
        top = min(MAX_ANTE, self.bankroll.balance // self.exposure)
        return top - top % STEP

    def _fit_ante(self):
        b = self.bankroll
        top = self.max_ante()
        if b.bet > top:
            b.bet = top
        if b.bet < MIN_ANTE:
            b.bet = MIN_ANTE

    def adjust_ante(self, delta):
        if self.state != BETTING:
            raise ValueError('not betting')
        self.bankroll.bet += delta
        self._fit_ante()
        return self.bankroll.bet

    def multiplier(self):
        """The multiplier on the call win of the hand being dealt: N players at the table, capped."""
        if not self.armed:
            return 1
        return max(1, min(self.rules.mult_cap, self.seats.count + 1))

    def deal(self):
        if self.state != BETTING:
            raise ValueError('not betting')
        self._fit_ante()
        if self.shoe.needs_shuffle():
            self.shoe.shuffle()
        self.round = Round(self.shoe, self.rules, self.bankroll.bet, self.multiplier()).deal()
        self.seats.deal(self.shoe)
        self.seats.act(self.round.flop(), self.rules)
        self.state = DECIDING
        return self.round

    def _deciding(self):
        if self.state != DECIDING:
            raise ValueError('no hand in play')

    def call(self, mult):
        self._deciding()
        self.round.call_(mult)
        self._settle()

    def fold(self):
        self._deciding()
        self.round.fold()
        self._settle()

    def _settle(self):
        r = self.round
        self.bankroll.apply(r.net)
        self.seats.settle(r.board, r.dv, r.ante, self.rules, r.mult)
        # John's rule: everyone at the table beat a qualified dealer -> next hand multiplied
        self.armed = (self.rules.mult_cap > 1 and self.seats.count > 0 and r.beat_qualified()
                      and self.seats.all_won())
        self.state = RESULT

    def next_hand(self):
        if self.state != RESULT:
            raise ValueError('no result to leave')
        self.round = None
        self.state = BROKE if self.is_broke() else BETTING
        self._fit_ante()

    def refill(self):
        if self.state != BROKE:
            raise ValueError('not broke')
        self.bankroll.refill()
        self._fit_ante()
        self.state = BETTING

    def stakes(self):
        """(chips to show as the bankroll, ante, call bet). In play the Ante is off the bankroll."""
        b = self.bankroll
        r = self.round
        if r is None:
            return b.balance, b.bet, 0
        if self.state == DECIDING:
            return b.balance - r.ante, r.ante, 0
        return b.balance, r.ante, r.call
