# Ultimate Texas Hold'em rules engine. Pure logic: no `machine` import.
#
# Ruling DR-042: equal Ante and Blind; two hole cards each; five community cards. Pre-flop the
# player raises 4x (or 3x) the Ante or checks; after the flop a checked player raises 2x or checks;
# after the turn and river a twice-checked player raises 1x or folds (losing Ante and Blind).
# Showdown: best five of seven. The dealer qualifies with a pair or better, else the Ante pushes.
# Player wins: Play 1:1, Ante 1:1 if the dealer qualified, Blind by BLIND_PAY for a straight or
# better (push below). Player loses: Ante (if the dealer qualified), Blind and Play lost. Tie: push.
# Also here: the published "simple strategy" (Wizard of Odds), used by the help screen, the seats
# (DR-044) and the simulator, and the river dealer-outs count for the hint (DR-042 addendum).

from poker import (evaluate, evaluate5, rank_value, name as hand_name, HIGH_CARD, PAIR, TWO_PAIR,
                   STRAIGHT, FLUSH, FULL_HOUSE, QUADS, STRAIGHT_FLUSH, ROYAL_FLUSH)

# category -> (numerator, denominator) paid on the Blind
BLIND_PAY = {STRAIGHT: (1, 1), FLUSH: (3, 2), FULL_HOUSE: (3, 1), QUADS: (10, 1),
             STRAIGHT_FLUSH: (50, 1), ROYAL_FLUSH: (500, 1)}

PREFLOP = 'preflop'      # two hole cards up, decide 4x / 3x / check
FLOP = 'flop'            # three community cards up, decide 2x / check
RIVER = 'river'          # all five up, decide 1x / fold
DONE = 'done'

WIN = 'win'
LOSE = 'lose'
PUSH = 'push'
FOLD = 'fold'


class Rules:
    def __init__(self, blind_pay=BLIND_PAY, qualify=PAIR, big_raise=4, small_big_raise=3):
        self.blind_pay = blind_pay
        self.qualify = qualify              # dealer needs at least this category for the Ante to count
        self.big_raise = big_raise          # pre-flop raises on offer
        self.small_big_raise = small_big_raise


def blind_win(ante, category, rules):
    """Chips the Blind pays for a winning hand of this category (0 = push)."""
    pay = rules.blind_pay.get(category)
    if not pay:
        return 0
    return ante * pay[0] // pay[1]


def resolve(pv, dv, ante, play_bet, rules):
    """Showdown: (outcome, net chips, dealer_qualified)."""
    qualified = dv[0] >= rules.qualify
    if pv > dv:
        net = play_bet + (ante if qualified else 0) + blind_win(ante, pv[0], rules)
        return WIN, net, qualified
    if pv < dv:
        return LOSE, -(play_bet + ante + (ante if qualified else 0)), qualified
    return PUSH, 0, qualified


# ---- published simple strategy (Wizard of Odds) -----------------------------------------------
def suited(a, b):
    return a // 13 == b // 13


def preflop_raise(hole):
    """Large raise with: any pair but 2s; any ace; K-2 suited or K-5 offsuit and up; Q-6 suited or
    Q-8 offsuit and up; J-8 suited or J-10 offsuit."""
    a, b = sorted([rank_value(c) for c in hole], reverse=True)
    s = suited(hole[0], hole[1])
    if a == b:
        return a >= 3
    if a == 14:
        return True
    if a == 13:
        return b >= 2 if s else b >= 5
    if a == 12:
        return b >= 6 if s else b >= 8
    if a == 11:
        return b >= 8 if s else b >= 10
    return False


def hidden_pair_or_better(hole, board):
    """A pair or better that uses at least one hole card: a pair on the board alone does not count,
    nor does a better kicker to the board's own pair."""
    v = evaluate(hole + board)
    if v[0] < PAIR:
        return False
    if len(board) == 3:
        board_pair = len(set(c % 13 for c in board)) < 3
        return not (v[0] == PAIR and board_pair)
    bv = evaluate5(board)
    if v[0] > bv[0]:
        return True
    if v[0] == PAIR and bv[0] == PAIR:
        return v[1] != bv[1]
    if v[0] == TWO_PAIR and bv[0] == TWO_PAIR:
        return (v[1], v[2]) != (bv[1], bv[2])
    return False


def flop_raise(hole, board):
    """Medium raise with: two pair or better; a hidden pair except pocket 2s; four to a flush with
    a hidden 10 or better in that suit."""
    v = evaluate(hole + board)
    if v[0] >= TWO_PAIR:
        return True
    if hidden_pair_or_better(hole, board):
        if not (hole[0] % 13 == hole[1] % 13 and rank_value(hole[0]) == 2):
            return True
    cards = hole + board
    for suit in range(4):
        same = [c for c in cards if c // 13 == suit]
        if len(same) >= 4 and any(c in hole and rank_value(c) >= 10 for c in same):
            return True
    return False


def dealer_outs(hole, board):
    """How many of the 45 unseen cards would, with the board, give the dealer a hand that beats the
    player's. The hint (DR-042 addendum); about 228 ms on the board (45 six-card evaluations)."""
    pv = evaluate(hole + board)
    seen = hole + board
    outs = 0
    for c in range(52):
        if c in seen:
            continue
        if evaluate([c] + board) > pv:
            outs += 1
    return outs


def river_raise(hole, board, outs=None):
    """Small raise with a hidden pair or better, or fewer than 21 dealer outs (pass the count, or
    None to skip that rule: the seats do, to stay cheap)."""
    if hidden_pair_or_better(hole, board):
        return True
    return outs is not None and outs < 21


def describe(value):
    """'pair of 9s', 'ace high', 'two pair', ... for the hand lines (same words as Stud)."""
    cat = value[0]
    if cat == HIGH_CARD:
        return rank_word(value[1]) + ' high'
    if cat == PAIR:
        return 'pair of ' + rank_word(value[1]) + 's'
    if cat == 2:
        return 'two pair'
    if cat == 3:
        return 'three ' + rank_word(value[1]) + 's'
    if cat == QUADS:
        return 'four ' + rank_word(value[1]) + 's'
    return hand_name(value)


def rank_word(v):
    return {14: 'ace', 13: 'king', 12: 'queen', 11: 'jack'}.get(v, str(v))


# ---- one hand -----------------------------------------------------------------------------------
class Round:
    def __init__(self, shoe, rules, ante):
        self.shoe = shoe
        self.rules = rules
        self.ante = ante                   # Blind equals the Ante
        self.play_bet = 0
        self.player = []
        self.dealer = []
        self.board = []
        self.state = PREFLOP
        self.outcome = None
        self.net = 0
        self.qualified = None
        self.pv = None
        self.dv = None

    def deal(self):
        s = self.shoe
        self.player = [s.draw(), s.draw()]
        self.dealer = [s.draw(), s.draw()]
        self.board = [s.draw() for _ in range(5)]
        return self

    def shown_board(self):
        """Community cards face up in the current phase."""
        if self.state == PREFLOP:
            return []
        if self.state == FLOP:
            return self.board[:3]
        return self.board

    def stake(self):
        return 2 * self.ante + self.play_bet

    def raise_(self, mult):
        """Pre-flop 4x or 3x, flop 2x, river 1x; then showdown."""
        if self.state == PREFLOP and mult in (self.rules.big_raise, self.rules.small_big_raise):
            pass
        elif self.state == FLOP and mult == 2:
            pass
        elif self.state == RIVER and mult == 1:
            pass
        else:
            raise ValueError('cannot raise %sx now' % mult)
        self.play_bet = self.ante * mult
        self._showdown()
        return self

    def check(self):
        if self.state == PREFLOP:
            self.state = FLOP
        elif self.state == FLOP:
            self.state = RIVER
        else:
            raise ValueError('cannot check at the river: raise or fold')
        return self

    def fold(self):
        if self.state != RIVER:
            raise ValueError('fold only at the river')
        self.state = DONE
        self.outcome = FOLD
        self.net = -2 * self.ante
        self.pv = evaluate(self.player + self.board)
        self.dv = evaluate(self.dealer + self.board)
        self.qualified = self.dv[0] >= self.rules.qualify
        return self

    def outs(self):
        """Dealer outs at the river (hint). Only meaningful in the RIVER state."""
        return dealer_outs(self.player, self.board)

    def _showdown(self):
        self.pv = evaluate(self.player + self.board)
        self.dv = evaluate(self.dealer + self.board)
        self.outcome, self.net, self.qualified = resolve(self.pv, self.dv, self.ante, self.play_bet, self.rules)
        self.state = DONE
