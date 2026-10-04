# Other players at the Caribbean table (DR-069): Ultimate's chip-stack seats. Each seat gets two
# real cards from the same deck after the player, dealer and board, plays the taught strategy at the
# flop with the player's Ante, settles against the same dealer hand with the same pays and the same
# armed multiplier, and keeps a chip count that starts at 1000 and refills silently. Cosmetic: never
# saved, never affects the player's cards, odds or payout. The seats are also the "everyone" of the
# multiplier rule (DR-064): it arms only when the player and every seat beat a qualified dealer.

from poker import evaluate
from caribbean_rules import advice, resolve, LOW, HIGH, WIN, FOLD

START = 1000
MAX_SEATS = 4


class Seats:
    def __init__(self, count=MAX_SEATS):
        self.count = max(0, min(MAX_SEATS, count))
        self.chips = [START] * self.count
        self.delta = [0] * self.count
        self.hands = [None] * self.count
        self.calls = [0] * self.count       # call multiple (0 = fold) once decided
        self.won = [False] * self.count

    def deal(self, shoe):
        for i in range(self.count):
            self.hands[i] = [shoe.draw(), shoe.draw()]
            self.delta[i] = 0
            self.calls[i] = 0
            self.won[i] = False

    def act(self, flop, rules):
        for i in range(self.count):
            a = advice(self.hands[i], flop)
            self.calls[i] = 0 if a is None else (rules.high if a == HIGH else rules.low)

    def status(self, i):
        """'4x', '2x' or 'fold' for a status line."""
        return 'fold' if not self.calls[i] else '%dx' % self.calls[i]

    def settle(self, board, dv, ante, rules, mult=1):
        """Showdown for every seat (run before the dealer's cards turn, HR-044)."""
        for i in range(self.count):
            if self.hands[i] is None:
                continue
            if self.chips[i] < ante * (1 + rules.high):
                self.chips[i] = START               # silent refill
            if not self.calls[i]:
                net = -ante
                self.won[i] = False
            else:
                pv = evaluate(self.hands[i] + board)
                outcome, net, q = resolve(pv, dv, ante, ante * self.calls[i], rules, mult)
                self.won[i] = outcome == WIN
            self.chips[i] += net
            self.delta[i] = net

    def all_won(self):
        for i in range(self.count):
            if not self.won[i]:
                return False
        return True

    def stack_height(self, i, per=200, cap=6):
        n = self.chips[i] // per
        return cap if n > cap else n
