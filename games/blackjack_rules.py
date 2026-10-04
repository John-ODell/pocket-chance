# Blackjack rules engine. Pure logic: no `machine` import, runs under CPython and MicroPython.
#
# Rulings: DR-009 S17, DR-010 3:2 rounding down, DR-011 6 decks / 75%, DR-012 hit, stand, double,
# DR-016 split once (same rank, aces one card each and stand, double after split, 21 after a split
# pays even money). Every rule is a parameter on Rules. Money is whole chips. The caller owns the
# bankroll; Round only reports the net change.

from cards import hand_value, Shoe

BLACKJACK = 'blackjack'
WIN = 'win'
LOSE = 'lose'
PUSH = 'push'
BUST = 'bust'      # player busted (a loss; separate so the UI can show banner_bust)

PLAYER = 'player'  # waiting for the player's action
DONE = 'done'      # round finished, outcome and net are set


class Rules:
    def __init__(self, decks=6, hit_soft_17=False, bj_num=3, bj_den=2,
                 penetration=0.75, dealer_peeks=True, double_any_two=True,
                 allow_split=True, double_after_split=True):
        self.decks = decks
        self.hit_soft_17 = hit_soft_17      # False = dealer stands on all 17s (S17)
        self.bj_num = bj_num                # blackjack pays bj_num : bj_den
        self.bj_den = bj_den
        self.penetration = penetration      # fraction of shoe dealt before reshuffle
        self.dealer_peeks = dealer_peeks    # dealer checks for blackjack on A or ten up-card
        self.double_any_two = double_any_two  # False = double only on hard 9, 10, 11
        self.allow_split = allow_split      # one split, same rank only (DR-016)
        self.double_after_split = double_after_split

    def new_shoe(self, rng):
        return Shoe(self.decks, rng, self.penetration)


def dealer_should_hit(cards, hit_soft_17):
    total, soft = hand_value(cards)
    if total < 17:
        return True
    if total == 17 and soft and hit_soft_17:
        return True
    return False


def is_blackjack(cards):
    return len(cards) == 2 and hand_value(cards)[0] == 21


def payout(bet, outcome, rules):
    """Net chips won (negative = lost) on a bet. Blackjack winnings round down."""
    if outcome == BLACKJACK:
        return bet * rules.bj_num // rules.bj_den
    if outcome == WIN:
        return bet
    if outcome == PUSH:
        return 0
    return -bet     # LOSE or BUST


class Round:
    """One round of blackjack: hit, stand, double, one split. No insurance or surrender.

    hands / bets / doubled are parallel lists (is_split says whether there are two), one entry per hand (two after a split).
    `active` is the hand being played. `player` and `bet` are the active hand's cards and the
    total stake, so single-hand callers need not know about splits.
    After DONE: `outcomes` and `nets` per hand, `outcome` and `net` overall.
    """

    def __init__(self, shoe, rules, bet):
        self.shoe = shoe
        self.rules = rules
        self.hands = [[]]
        self.bets = [bet]
        self.doubled = [False]
        self.dealer = []
        self.active = 0
        self.is_split = False
        self.state = PLAYER
        self.outcome = None
        self.outcomes = [None]
        self.net = 0
        self.nets = [0]

    @property
    def player(self):
        return self.hands[self.active]

    @player.setter
    def player(self, cards):
        self.hands[self.active] = cards

    @property
    def bet(self):
        """Total chips at stake across all hands."""
        return sum(self.bets)

    def deal(self):
        s = self.shoe
        p = self.hands[0]
        p.append(s.draw())
        self.dealer.append(s.draw())   # dealer's first card is the up-card
        p.append(s.draw())
        self.dealer.append(s.draw())   # second card is the hole card
        p_bj = is_blackjack(p)
        d_bj = is_blackjack(self.dealer)
        up = self.dealer[0]
        peek_now = self.rules.dealer_peeks and (hand_value([up])[0] >= 10 or up % 13 == 0)
        if p_bj or (d_bj and peek_now):
            # A player blackjack always ends the round now. A dealer blackjack ends it
            # now only when the dealer peeks (A or ten up-card).
            if p_bj and d_bj:
                self._finish([PUSH])
            elif p_bj:
                self._finish([BLACKJACK])
            else:
                self._finish([LOSE])
        return self

    def hole_hidden(self):
        """True while the UI must keep the dealer's second card face down."""
        return self.state == PLAYER

    # ---- what the player may do -------------------------------------------------------------
    def can_double(self):
        if self.state != PLAYER or len(self.player) != 2:
            return False
        if self.is_split and not self.rules.double_after_split:
            return False
        if self.rules.double_any_two:
            return True
        total, soft = hand_value(self.player)
        return (not soft) and 9 <= total <= 11

    def can_split(self):
        """First two cards of the same rank, once per round (ten-value cards must match in rank)."""
        if self.state != PLAYER or self.is_split or not self.rules.allow_split:
            return False
        p = self.player
        return len(p) == 2 and p[0] % 13 == p[1] % 13

    # ---- actions -----------------------------------------------------------------------------
    def hit(self):
        self._need_player()
        self.player.append(self.shoe.draw())
        total = hand_value(self.player)[0]
        if total > 21:
            self.outcomes[self.active] = BUST
            self._advance()
        elif total == 21:
            self._advance()
        return self

    def stand(self):
        self._need_player()
        self._advance()
        return self

    def double(self):
        """Double this hand's bet, take exactly one card, then stand. Caller checks the bankroll."""
        if not self.can_double():
            raise ValueError('cannot double')
        i = self.active
        self.bets[i] *= 2
        self.doubled[i] = True
        self.player.append(self.shoe.draw())
        if hand_value(self.player)[0] > 21:
            self.outcomes[i] = BUST
        self._advance()
        return self

    def split(self):
        """Split the pair into two hands of one card each, deal one card to each. Caller checks
        the bankroll covers the second bet. Split aces get their one card and both hands stand."""
        if not self.can_split():
            raise ValueError('cannot split')
        c0, c1 = self.hands[0]
        s = self.shoe
        self.hands = [[c0, s.draw()], [c1, s.draw()]]
        self.bets = [self.bets[0], self.bets[0]]
        self.doubled = [False, False]
        self.outcomes = [None, None]
        self.nets = [0, 0]
        self.is_split = True
        self.active = 0
        if c0 % 13 == 0:                      # aces: one card each, no further play
            self.active = len(self.hands)
            self._settle()
        elif hand_value(self.hands[0])[0] == 21:
            self._advance()                   # 21 after a split stands automatically
        return self

    # ---- internals ---------------------------------------------------------------------------
    def _need_player(self):
        if self.state != PLAYER:
            raise ValueError('round is over')

    def _advance(self):
        """Move to the next hand, or settle the round when none is left."""
        self.active += 1
        while self.active < len(self.hands):
            if hand_value(self.hands[self.active])[0] == 21:
                self.active += 1              # a 21 after a split needs no decision
            else:
                return
        self._settle()

    def _settle(self):
        live = [i for i in range(len(self.hands)) if self.outcomes[i] is None]
        if live:
            while dealer_should_hit(self.dealer, self.rules.hit_soft_17):
                self.dealer.append(self.shoe.draw())
        d = hand_value(self.dealer)[0]
        d_bj = is_blackjack(self.dealer)      # only reachable when dealer_peeks is False
        outcomes = []
        for i in range(len(self.hands)):
            if self.outcomes[i] is not None:
                outcomes.append(self.outcomes[i])
                continue
            p = hand_value(self.hands[i])[0]
            if d_bj:
                outcomes.append(LOSE)
            elif d > 21 or p > d:
                outcomes.append(WIN)
            elif p == d:
                outcomes.append(PUSH)
            else:
                outcomes.append(LOSE)
        self.active = len(self.hands) - 1
        self._finish(outcomes)

    def _finish(self, outcomes):
        self.state = DONE
        self.outcomes = outcomes
        self.nets = [payout(self.bets[i], outcomes[i], self.rules) for i in range(len(outcomes))]
        self.net = sum(self.nets)
        if len(outcomes) == 1:
            self.outcome = outcomes[0]
        elif self.net > 0:
            self.outcome = WIN
        elif self.net < 0:
            self.outcome = BUST if outcomes[0] == BUST and outcomes[1] == BUST else LOSE
        else:
            self.outcome = PUSH
