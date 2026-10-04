# Caribbean Stud session: ante limits against the shared bankroll (DR-028), the hand flow, and
# what the screen shows. Pure logic: no `machine` import.

from stud_rules import Rules, Round, new_deck, DECISION, DONE, FOLD

MIN_ANTE, MAX_ANTE, STEP = 5, 100, 5
EXPOSURE = 3                 # ante + 2x raise: the bankroll must cover three antes when dealt

BETTING = 'betting'
DECIDING = 'deciding'
RESULT = 'result'
BROKE = 'broke'


class StudTable:
    def __init__(self, rng, bankroll, rules=None):
        self.rules = rules or Rules()
        self.bankroll = bankroll
        self.shoe = new_deck(rng)
        self.round = None
        self._fit_ante()
        self.state = BROKE if self.is_broke() else BETTING

    def is_broke(self):
        return self.bankroll.balance < MIN_ANTE * EXPOSURE

    def max_ante(self):
        """Largest ante the bankroll can play out (ante plus raise), in steps of 5, capped at 100."""
        top = min(MAX_ANTE, self.bankroll.balance // EXPOSURE)
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

    def deal(self):
        if self.state != BETTING:
            raise ValueError('not betting')
        self._fit_ante()
        if self.shoe.needs_shuffle():
            self.shoe.shuffle()
        self.round = Round(self.shoe, self.rules, self.bankroll.bet).deal()
        self.state = DECIDING
        return self.round

    def fold(self):
        self._deciding()
        self.round.fold()
        self._settle()

    def raise_(self):
        self._deciding()
        self.round.raise_()
        self._settle()

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
        """(chips to show as the bankroll, ante, raise). In play the stake is off the bankroll."""
        b = self.bankroll
        r = self.round
        if r is None:
            return b.balance, b.bet, 0
        if self.state == DECIDING:
            return b.balance - r.ante, r.ante, 0
        return b.balance, r.ante, r.raise_bet

    def _deciding(self):
        if self.state != DECIDING:
            raise ValueError('not deciding')

    def _settle(self):
        self.bankroll.apply(self.round.net)
        self.state = RESULT
