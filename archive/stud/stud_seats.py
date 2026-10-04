# Other players at the Caribbean Stud table (ruling DR-041): chip stacks only. Each seat is dealt
# five real cards from the same deck after the player and dealer, plays the published basic strategy
# (stud_rules.advice) against the same dealer hand with the player's ante, and keeps a chip count
# that starts at 1000, moves by its real results and refills silently when it cannot cover a hand.
# Cosmetic: never saved, never affects the player's cards, odds or payout (every card is equally
# likely wherever it is dealt). Pure logic: no `machine` import.

from poker import evaluate5
from stud_rules import advice, resolve, FOLD

START = 1000
MAX_SEATS = 5


class Seats:
    def __init__(self, count=MAX_SEATS):
        self.count = max(0, min(MAX_SEATS, count))
        self.chips = [START] * self.count
        self.delta = [0] * self.count          # result of the last hand, 0 until settled
        self.hands = [None] * self.count

    def deal(self, shoe):
        """Five cards per seat, after the player's and dealer's ten. Clears the markers."""
        for i in range(self.count):
            self.hands[i] = [shoe.draw() for _ in range(5)]
            self.delta[i] = 0

    def settle(self, dealer, dv, ante, rules):
        """Play every seat against the dealer's hand: fold or raise by basic strategy, then the
        same payout rules as the player (stud_rules.resolve)."""
        up = dealer[0]
        for i in range(self.count):
            cards = self.hands[i]
            if cards is None:
                continue
            if self.chips[i] < ante * (1 + rules.raise_mult):
                self.chips[i] = START               # silent refill (DR-041)
            pv = evaluate5(cards)
            if advice(cards, pv, up):
                outcome, net = resolve(pv, dv, ante, rules)
            else:
                outcome, net = FOLD, -ante
            self.chips[i] += net
            self.delta[i] = net

    def stack_height(self, i, per=200, cap=6):
        """Chip lines to draw for seat i: one per `per` chips, at most `cap`."""
        n = self.chips[i] // per
        return cap if n > cap else n
