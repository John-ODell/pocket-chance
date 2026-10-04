# Ultimate Texas Hold'em session: Ante limits against the shared bankroll (DR-046: 5 to 50, capped
# at a sixth of the bankroll so Ante + Blind + 4x Play is always covered), the hand flow with the
# seats (DR-044), and what the screen shows. Pure logic: no `machine` import.

from cards import Shoe
from holdem_rules import Rules, Round, PREFLOP, FLOP, RIVER, DONE
from holdem_seats import Seats

MIN_ANTE, MAX_ANTE, STEP = 5, 50, 5
EXPOSURE = 6                 # Ante + Blind + 4x Play

BETTING = 'betting'
RESULT = 'result'
BROKE = 'broke'
# while a hand is in play the table's state is the round's: PREFLOP, FLOP, RIVER


class HoldemTable:
    def __init__(self, rng, bankroll, rules=None, seats=4, hint=True):
        self.rules = rules or Rules()
        self.bankroll = bankroll
        self.shoe = Shoe(1, rng, penetration=0.0)       # a fresh deck every hand
        self.round = None
        self.seats = Seats(seats)
        self.hint = hint                                 # DR-042 addendum: river outs count
        self.outs = None                                 # computed once per hand at the river
        self._fit_ante()
        self.state = BROKE if self.is_broke() else BETTING

    def is_broke(self):
        return self.bankroll.balance < MIN_ANTE * EXPOSURE

    def max_ante(self):
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
        self.seats.deal(self.shoe)
        self.outs = None
        self.state = PREFLOP
        return self.round

    # ---- decisions --------------------------------------------------------------------------
    def _in_play(self):
        if self.state not in (PREFLOP, FLOP, RIVER):
            raise ValueError('no hand in play')

    def raise_(self, mult):
        self._in_play()
        self.round.raise_(mult)
        self._seats_through(self.state)
        self._settle()

    def check(self):
        self._in_play()
        if self.state == PREFLOP:
            self.seats.act_preflop(self.rules)
            self.round.check()
            self.state = FLOP
        elif self.state == FLOP:
            self.seats.act_flop(self.round.board[:3])
            self.round.check()
            self.state = RIVER
            if self.hint:
                self.outs = self.round.outs()
        else:
            raise ValueError('cannot check at the river')

    def fold(self):
        if self.state != RIVER:
            raise ValueError('fold only at the river')
        self.round.fold()
        self._seats_through(RIVER)
        self._settle()

    def _seats_through(self, phase):
        """Let the seats make the decisions the player's action skipped past."""
        if phase == PREFLOP:
            self.seats.act_preflop(self.rules)
            self.seats.act_flop(self.round.board[:3])
            self.seats.act_river(self.round.board)
        elif phase == FLOP:
            self.seats.act_flop(self.round.board[:3])
            self.seats.act_river(self.round.board)
        else:
            self.seats.act_river(self.round.board)

    def _settle(self):
        r = self.round
        self.bankroll.apply(r.net)
        self.seats.settle(r.board, r.dv, r.ante, self.rules)
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
        """(chips to show as the bankroll, ante, play bet). In play the stake is off the bankroll."""
        b = self.bankroll
        r = self.round
        if r is None:
            return b.balance, b.bet, 0
        if self.state in (PREFLOP, FLOP, RIVER):
            return b.balance - 2 * r.ante, r.ante, 0
        return b.balance, r.ante, r.play_bet
