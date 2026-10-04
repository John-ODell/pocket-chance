# Other players at the baccarat table (ruling DR-055): chip stacks only. Every seat stakes 20 a
# coup on the side its habit picks and wins or loses on the coup the player sees, with the same
# pays. Chips start at 1000, refill silently when a stake cannot be covered, and are never saved.
# Cosmetic: the seats draw no cards and never touch the player's result. Pure logic.

from baccarat_rules import PLAYER, BANKER, TIE, settle

START = 1000
MAX_SEATS = 5
STAKE = 20
# habits: seat 0 always Banker, 1 always Player, 2 follows the last winner, 3 bets against it,
# 4 Banker but Tie every fifth coup (DR-055)
ALWAYS_BANKER, ALWAYS_PLAYER, FOLLOW, AGAINST, TIE_FIFTH = range(5)


class Seats:
    def __init__(self, count=MAX_SEATS):
        self.count = max(0, min(MAX_SEATS, count))
        self.chips = [START] * self.count
        self.delta = [0] * self.count           # last coup's result
        self.settled = [False] * self.count     # True once a marker should show
        self.sides = [PLAYER] * self.count      # the side each seat is on this coup
        self.last = None                        # last non-tie winner
        self.coups = 0

    def place(self):
        """Pick every seat's side for the coming coup and clear the markers."""
        self.coups += 1
        last = BANKER if self.last is None else self.last
        for i in range(self.count):
            if i == ALWAYS_BANKER:
                side = BANKER
            elif i == ALWAYS_PLAYER:
                side = PLAYER
            elif i == FOLLOW:
                side = last
            elif i == AGAINST:
                side = PLAYER if last == BANKER else BANKER
            else:
                side = TIE if self.coups % 5 == 0 else BANKER
            self.sides[i] = side
            self.delta[i] = 0
            self.settled[i] = False

    def settle(self, winner):
        for i in range(self.count):
            if self.chips[i] < STAKE:
                self.chips[i] = START           # silent refill
            net = settle(self.sides[i], STAKE, winner)
            self.chips[i] += net
            self.delta[i] = net
            self.settled[i] = True
        if winner != TIE:
            self.last = winner

    def stack_height(self, i, per=200, cap=6):
        n = self.chips[i] // per
        return cap if n > cap else n
