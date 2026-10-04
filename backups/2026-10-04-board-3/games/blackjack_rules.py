# Blackjack rules engine. Pure logic: no `machine` import, runs under CPython and MicroPython.
#
# Every house rule that has not been approved yet is a parameter on Rules, not a constant.
# Money is whole chips. The caller owns the bankroll; Round only reports the net change.

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
                 penetration=0.75, dealer_peeks=True, double_any_two=True):
        self.decks = decks
        self.hit_soft_17 = hit_soft_17      # False = dealer stands on all 17s (S17)
        self.bj_num = bj_num                # blackjack pays bj_num : bj_den
        self.bj_den = bj_den
        self.penetration = penetration      # fraction of shoe dealt before reshuffle
        self.dealer_peeks = dealer_peeks    # dealer checks for blackjack on A or ten up-card
        self.double_any_two = double_any_two  # False = double only on hard 9, 10, 11

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
    """One hand of blackjack: hit, stand, double. No split, insurance or surrender."""

    def __init__(self, shoe, rules, bet):
        self.shoe = shoe
        self.rules = rules
        self.bet = bet
        self.player = []
        self.dealer = []
        self.state = PLAYER
        self.outcome = None
        self.net = 0
        self.doubled = False

    def deal(self):
        s = self.shoe
        self.player.append(s.draw())
        self.dealer.append(s.draw())   # dealer's first card is the up-card
        self.player.append(s.draw())
        self.dealer.append(s.draw())   # second card is the hole card
        p_bj = is_blackjack(self.player)
        d_bj = is_blackjack(self.dealer)
        up = self.dealer[0]
        peek_now = self.rules.dealer_peeks and (hand_value([up])[0] >= 10 or up % 13 == 0)
        if p_bj or (d_bj and peek_now):
            # A player blackjack always ends the round now. A dealer blackjack ends it
            # now only when the dealer peeks (A or ten up-card).
            if p_bj and d_bj:
                self._finish(PUSH)
            elif p_bj:
                self._finish(BLACKJACK)
            else:
                self._finish(LOSE)
        return self

    def hole_hidden(self):
        """True while the UI must keep the dealer's second card face down."""
        return self.state == PLAYER

    def can_double(self):
        if self.state != PLAYER or len(self.player) != 2:
            return False
        if self.rules.double_any_two:
            return True
        total, soft = hand_value(self.player)
        return (not soft) and 9 <= total <= 11

    def hit(self):
        self._need_player()
        self.player.append(self.shoe.draw())
        total = hand_value(self.player)[0]
        if total > 21:
            self._finish(BUST)
        elif total == 21:
            self._dealer_play()
        return self

    def stand(self):
        self._need_player()
        self._dealer_play()
        return self

    def double(self):
        """Double the bet, take exactly one card, then stand. Caller checks the bankroll."""
        if not self.can_double():
            raise ValueError('cannot double')
        self.bet *= 2
        self.doubled = True
        self.player.append(self.shoe.draw())
        if hand_value(self.player)[0] > 21:
            self._finish(BUST)
        else:
            self._dealer_play()
        return self

    def _need_player(self):
        if self.state != PLAYER:
            raise ValueError('round is over')

    def _dealer_play(self):
        while dealer_should_hit(self.dealer, self.rules.hit_soft_17):
            self.dealer.append(self.shoe.draw())
        p = hand_value(self.player)[0]
        d = hand_value(self.dealer)[0]
        if is_blackjack(self.dealer):   # only reachable when dealer_peeks is False
            self._finish(LOSE)
        elif d > 21 or p > d:
            self._finish(WIN)
        elif p == d:
            self._finish(PUSH)
        else:
            self._finish(LOSE)

    def _finish(self, outcome):
        self.state = DONE
        self.outcome = outcome
        self.net = payout(self.bet, outcome, self.rules)
