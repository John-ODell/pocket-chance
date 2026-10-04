# In-memory bankroll and bet limits. Pure logic: no `machine` import.
# Rulings: DR-013 (start 1000, free refill when broke), DR-014 (bets 5 to 500 in steps of 5).
# Saving to flash is NOT here: the file format and corruption handling wait on DR-007 and DR-008.

START_BANKROLL = 1000
MIN_BET = 5
MAX_BET = 500
BET_STEP = 5


class Bankroll:
    def __init__(self, balance=START_BANKROLL, start=START_BANKROLL,
                 min_bet=MIN_BET, max_bet=MAX_BET, step=BET_STEP):
        self.balance = balance
        self.start = start
        self.min_bet = min_bet
        self.max_bet = max_bet
        self.step = step
        self.bet = min_bet

    def is_broke(self):
        """True when the player cannot cover the minimum bet."""
        return self.balance < self.min_bet

    def refill(self):
        """Free refill (DR-013): resets the balance only."""
        self.balance = self.start
        self.bet = self.min_bet

    def top_bet(self):
        """Highest bet allowed right now: capped by max_bet and by the balance, in whole steps."""
        top = self.balance if self.balance < self.max_bet else self.max_bet
        return top - top % self.step

    def clamp_bet(self):
        top = self.top_bet()
        if self.bet > top:
            self.bet = top
        if self.bet < self.min_bet:
            self.bet = self.min_bet
        return self.bet

    def adjust_bet(self, delta):
        """Change the bet by `delta` chips (use multiples of the step); result stays in limits."""
        self.bet += delta
        top = self.top_bet()
        if self.bet > top:
            self.bet = top
        if self.bet < self.min_bet:
            self.bet = self.min_bet
        return self.bet

    def can_cover_double(self, bet):
        """A double adds a second bet equal to the first (DR-014), so twice the bet must be covered."""
        return self.balance >= 2 * bet

    def apply(self, net):
        self.balance += net
