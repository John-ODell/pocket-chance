# Other players at the Hold'em table (ruling DR-044 rev 2): chip stacks only. Each seat gets two
# real cards from the same deck after the player, dealer and board (17 of 52 for four seats), plays
# the published simple strategy at the three decision points against the same community and dealer
# cards with the player's Ante, and keeps a chip count that starts at 1000, moves by real results
# and refills silently. Seats skip the river outs count (228 ms each) and use the hidden-pair rule
# alone: cosmetic, never saved, never affects the player's cards, odds or payout.
# HR-044: the showdown's evaluations run before the first dealer flip, never inside a 300 ms gap.

from poker import evaluate
from holdem_rules import preflop_raise, flop_raise, river_raise, resolve, FOLD

START = 1000
MAX_SEATS = 4


class Seats:
    def __init__(self, count=MAX_SEATS):
        self.count = max(0, min(MAX_SEATS, count))
        self.chips = [START] * self.count
        self.delta = [0] * self.count
        self.hands = [None] * self.count
        self.play = [0] * self.count        # Play bet multiple decided so far (0 = none yet)
        self.folded = [False] * self.count

    def deal(self, shoe):
        for i in range(self.count):
            self.hands[i] = [shoe.draw(), shoe.draw()]
            self.delta[i] = 0
            self.play[i] = 0
            self.folded[i] = False

    def act_preflop(self, rules):
        """Seats that raise 4x do so now; the rest check."""
        for i in range(self.count):
            if preflop_raise(self.hands[i]):
                self.play[i] = rules.big_raise

    def act_flop(self, board3):
        for i in range(self.count):
            if self.play[i] == 0 and flop_raise(self.hands[i], board3):
                self.play[i] = 2

    def act_river(self, board):
        for i in range(self.count):
            if self.play[i] == 0:
                if river_raise(self.hands[i], board):
                    self.play[i] = 1
                else:
                    self.folded[i] = True

    def status(self, i):
        """'4x', '2x', '1x', 'fold' or 'check' for the status line under a stack."""
        if self.folded[i]:
            return 'fold'
        if self.play[i]:
            return '%dx' % self.play[i]
        return 'check'

    def settle(self, board, dv, ante, rules):
        """Showdown for every seat (run before the dealer's cards are turned, HR-044)."""
        for i in range(self.count):
            if self.hands[i] is None:
                continue
            if self.chips[i] < ante * 6:
                self.chips[i] = START               # silent refill
            if self.folded[i]:
                net = -2 * ante
            else:
                pv = evaluate(self.hands[i] + board)
                outcome, net, q = resolve(pv, dv, ante, ante * self.play[i], rules)
            self.chips[i] += net
            self.delta[i] = net

    def stack_height(self, i, per=200, cap=6):
        n = self.chips[i] // per
        return cap if n > cap else n
