# "Caribbean" as John wants it played (DR-062, DR-063, DR-064 and his rulings of 2026-10-06):
# Casino Hold'em with a low or high call. Pure logic: no `machine` import.
#
# Ante. Two cards to the player, two to the dealer, five table cards. The first three table cards
# turn; the player folds (losing the Ante), calls LOW (2x the Ante) or HIGH (4x). The last two turn.
# Best five of seven. The dealer qualifies with a pair of fours or better; if not, EVERY bet pushes
# (John's ruling). Qualified and beaten: the Ante pays by ANTE_PAY and the call 1:1. Dealer wins:
# Ante and call lost. Tie: push.
# Multiplier (John's WSOP rule, toned down, his ruling of 2026-10-06): when the player and every seat
# beat a qualified dealer, the next hand pays its winners three times the whole win (Ante table pay
# and call together). It lasts exactly one hand, never stacks and is never saved; a hand that does
# not win gets nothing extra. It fires about one hand in 25.
# Also here: the strategy the help screen teaches and the seats play, and the simulator's numbers
# (tools/casino_holdem_edge.py): about 5% of the Ante with this strategy, see pm/STATUS.md.

from poker import evaluate, evaluate5, rank_value, PAIR, TWO_PAIR, FLUSH, FULL_HOUSE, QUADS, STRAIGHT_FLUSH, ROYAL_FLUSH

ANTE_PAY = {ROYAL_FLUSH: 100, STRAIGHT_FLUSH: 20, QUADS: 10, FULL_HOUSE: 3, FLUSH: 2}   # else 1:1

DECIDING = 'deciding'     # flop shown: fold, low or high
DONE = 'done'

WIN = 'win'
LOSE = 'lose'
PUSH = 'push'
FOLD = 'fold'

LOW, HIGH = 1, 2          # advice() values; the call multiples are in Rules


class Rules:
    def __init__(self, low=2, high=4, qualify_pair=4, mult_cap=3):
        self.low = low                    # call multiples, in Antes
        self.high = high
        self.qualify_pair = qualify_pair  # dealer needs at least a pair of this rank
        self.mult_cap = mult_cap          # the armed multiplier on a winning hand's whole payout (0 = off)


def qualifies(dv, rules):
    if dv[0] > PAIR:
        return True
    return dv[0] == PAIR and dv[1] >= rules.qualify_pair


def ante_win(ante, category):
    return ante * ANTE_PAY.get(category, 1)


def resolve(pv, dv, ante, call, rules, mult=1):
    """Showdown for a player who called `call` chips. Returns (outcome, net, qualified)."""
    qualified = qualifies(dv, rules)
    if not qualified:
        return PUSH, 0, False
    if pv > dv:
        return WIN, (ante_win(ante, pv[0]) + call) * mult, True
    if pv < dv:
        return LOSE, -(ante + call), True
    return PUSH, 0, True


# ---- the taught strategy (the simulator's best simple rule set) ---------------------------------
def has_draw(hole, flop):
    """Four to a flush or four to a straight (open or inside) using at least one hole card."""
    cards = hole + flop
    suits = [0, 0, 0, 0]
    for c in cards:
        suits[c // 13] += 1
    for c in hole:
        if suits[c // 13] >= 4:
            return True
    ranks = set()
    for c in cards:
        ranks.add(rank_value(c))
    if 14 in ranks:
        ranks.add(1)
    hole_ranks = set(rank_value(c) for c in hole)
    for low in range(1, 11):
        run = [r for r in range(low, low + 5) if r in ranks]
        if len(run) >= 4 and hole_ranks & set(run):
            return True
    return False


def advice(hole, flop):
    """FOLD (None), LOW or HIGH at the flop: HIGH with two pair or better, or a pair using one of
    your cards; LOW with four to a flush or a straight, or a card of yours above every table card;
    otherwise fold."""
    v = evaluate5(hole + flop)
    hole_ranks = [rank_value(c) for c in hole]
    if v[0] >= TWO_PAIR:
        return HIGH
    if v[0] == PAIR:
        return HIGH if v[1] in hole_ranks else LOW
    if has_draw(hole, flop):
        return LOW
    if max(hole_ranks) > max(rank_value(c) for c in flop):
        return LOW
    return None


# ---- one hand -----------------------------------------------------------------------------------
class Round:
    def __init__(self, shoe, rules, ante, mult=1):
        self.shoe = shoe
        self.rules = rules
        self.ante = ante
        self.mult = mult                   # the armed multiplier for this hand's whole win
        self.call = 0
        self.player = []
        self.dealer = []
        self.board = []
        self.state = DECIDING
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

    def flop(self):
        return self.board[:3]

    def call_(self, mult):
        """LOW or HIGH call (in Antes), then the showdown."""
        if self.state != DECIDING or mult not in (self.rules.low, self.rules.high):
            raise ValueError('cannot call %sx now' % mult)
        self.call = self.ante * mult
        self._showdown()
        self.outcome, self.net, self.qualified = resolve(self.pv, self.dv, self.ante, self.call,
                                                        self.rules, self.mult)
        return self

    def fold(self):
        if self.state != DECIDING:
            raise ValueError('cannot fold now')
        self._showdown()
        self.outcome = FOLD
        self.net = -self.ante
        self.qualified = qualifies(self.dv, self.rules)
        return self

    def beat_qualified(self):
        """True when this hand beat a dealer who qualified (the multiplier's condition)."""
        return self.outcome == WIN

    def _showdown(self):
        self.pv = evaluate(self.player + self.board)
        self.dv = evaluate(self.dealer + self.board)
        self.state = DONE
