# One blackjack table: ties the Bankroll, the Shoe and Round together.
# Pure logic: no `machine` import. The screen code calls these methods and draws the result.

from bankroll import Bankroll
from blackjack_rules import Rules, Round, PLAYER, DONE

BETTING = 'betting'
PLAYING = 'playing'
RESULT = 'result'
BROKE = 'broke'


class Table:
    def __init__(self, rng, rules=None, bankroll=None):
        self.rules = rules or Rules()
        self.bankroll = bankroll or Bankroll()
        self.rng = rng
        self.shoe = self.rules.new_shoe(rng)
        self.round = None
        self.shuffled = False   # True when the shoe was reshuffled before the last deal
        self.state = BROKE if self.bankroll.is_broke() else BETTING

    def adjust_bet(self, delta):
        if self.state != BETTING:
            raise ValueError('not betting')
        return self.bankroll.adjust_bet(delta)

    def deal(self):
        """Start a round with the current bet. Returns the Round (may already be finished)."""
        if self.state != BETTING:
            raise ValueError('not betting')
        bank = self.bankroll
        bank.clamp_bet()
        self.shuffled = False
        if self.shoe.needs_shuffle():
            self.shoe.shuffle()
            self.shuffled = True
        self.round = Round(self.shoe, self.rules, bank.bet).deal()
        self._check_done()
        return self.round

    def can_double(self):
        r = self.round
        return (self.state == PLAYING and r.can_double()
                and self.bankroll.can_cover_double(r.bet))

    def hit(self):
        self.round.hit()
        self._check_done()

    def stand(self):
        self.round.stand()
        self._check_done()

    def double(self):
        if not self.can_double():
            raise ValueError('cannot double')
        self.round.double()
        self._check_done()

    def next_hand(self):
        """Leave the result screen. Goes to BROKE if the minimum bet can't be covered."""
        if self.state != RESULT:
            raise ValueError('no result to leave')
        self.round = None
        self.state = BROKE if self.bankroll.is_broke() else BETTING
        self.bankroll.clamp_bet()

    def stakes(self):
        """(chips to show as the bankroll, chips to show as the bet). While a hand is in play the
        stake sits on the table, so it is shown taken off the bankroll; after a double it is 2x."""
        bank = self.bankroll
        r = self.round
        if r is None:
            return bank.balance, bank.bet
        if self.state == PLAYING:
            return bank.balance - r.bet, r.bet
        return bank.balance, r.bet

    def refill(self):
        if self.state != BROKE:
            raise ValueError('not broke')
        self.bankroll.refill()
        self.state = BETTING

    def _check_done(self):
        if self.round.state == DONE:
            self.bankroll.apply(self.round.net)
            self.state = RESULT
        else:
            self.state = PLAYING
