# Baccarat session: the stake and side against the shared bankroll (DR-053, DR-054), the shoe
# (eight decks, cut card, DR-051), the seats (DR-055) and the result history (DR-060). Pure logic.

from cards import Shoe
from baccarat_rules import Coup, PLAYER, BANKER, TIE, DECKS, PENETRATION, settle
from baccarat_seats import Seats

MIN_STAKE, MAX_STAKE, STEP = 5, 100, 5
HISTORY = 12

BETTING = 'betting'
RESULT = 'result'
BROKE = 'broke'


class BaccaratTable:
    def __init__(self, rng, bankroll, seats=5):
        self.bankroll = bankroll
        self.shoe = Shoe(DECKS, rng, penetration=PENETRATION)
        self.side = PLAYER                      # resets to Player on entry (DR-056)
        self.coup = None
        self.net = 0
        self.seats = Seats(seats)
        self.history = []                       # last HISTORY winners, oldest first
        self.shuffled = False                   # True when the last deal began a new shoe
        self._fit_stake()
        self.state = BROKE if self.is_broke() else BETTING

    def is_broke(self):
        return self.bankroll.balance < MIN_STAKE

    def max_stake(self):
        top = min(MAX_STAKE, self.bankroll.balance)
        return top - top % STEP

    def _fit_stake(self):
        b = self.bankroll
        top = self.max_stake()
        if b.bet > top:
            b.bet = top
        if b.bet < MIN_STAKE:
            b.bet = MIN_STAKE

    def _betting(self):
        if self.state != BETTING:
            raise ValueError('not betting')

    def adjust_stake(self, delta):
        self._betting()
        self.bankroll.bet += delta
        self._fit_stake()
        return self.bankroll.bet

    def select(self, delta):
        """Move the chosen side: PLAYER, TIE, BANKER left to right (DR-053)."""
        self._betting()
        order = (PLAYER, TIE, BANKER)
        i = order.index(self.side) + delta
        self.side = order[max(0, min(2, i))]
        return self.side

    def deal(self):
        """Deal and settle the whole coup; the screen reveals it card by card (DR-052)."""
        self._betting()
        self._fit_stake()
        self.shuffled = self.shoe.needs_shuffle()
        if self.shuffled:
            self.shoe.shuffle()
        self.seats.place()
        self.coup = Coup(self.shoe)
        w = self.coup.winner
        self.net = settle(self.side, self.bankroll.bet, w)
        self.bankroll.apply(self.net)
        self.seats.settle(w)
        self.history.append(w)
        if len(self.history) > HISTORY:
            del self.history[0]
        self.state = RESULT
        return self.coup

    def next_coup(self):
        if self.state != RESULT:
            raise ValueError('no result to leave')
        self.coup = None
        self.state = BROKE if self.is_broke() else BETTING
        self._fit_stake()

    def refill(self):
        if self.state != BROKE:
            raise ValueError('not broke')
        self.bankroll.refill()
        self._fit_stake()
        self.state = BETTING

    def stakes(self, revealing=False):
        """(chips to show as the bankroll, stake). While the cards are turning the stake is off the
        bankroll and the result not yet added."""
        b = self.bankroll
        if revealing and self.coup is not None:
            return b.balance - self.net - b.bet, b.bet
        return b.balance, b.bet
