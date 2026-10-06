# Punto banco baccarat rules (ruling DR-051) and pays (DR-051, DR-059). Pure logic: no `machine`
# import. Cards are the ints from cards.py (rank = c % 13, 0 = ace).
#
# Aces count 1, tens and faces 0, totals modulo 10. Two cards each, Player first. A natural 8 or 9
# ends the coup. Otherwise the Player draws on 0-5 and stands on 6-7; the Banker draws by the
# tableau below. Player pays 1:1, Banker 1:1 less 5% (paid stake * 19 // 20, DR-059), Tie 8:1; a
# tie pushes the Player and Banker bets. Edges (tools/baccarat_edge.py, exact): Banker 1.06%,
# Player 1.24%, Tie 14.36%.

PLAYER, BANKER, TIE = 0, 1, 2
SIDE_NAMES = ('PLAYER', 'BANKER', 'TIE')
TIE_PAY = 8
DECKS = 8
CUT_CARD = 14                       # cards left when the cut card is reached (DR-051)
PENETRATION = 1.0 - CUT_CARD / (52.0 * DECKS)


def points(card):
    r = card % 13
    return 0 if r >= 9 else r + 1


def total(cards):
    t = 0
    for c in cards:
        t += points(c)
    return t % 10


def banker_draws(b, player_third):
    """The Banker's rule. `player_third` is the value of the Player's third card, or None when the
    Player stood."""
    if player_third is None:
        return b <= 5
    v = player_third
    if b <= 2:
        return True
    if b == 3:
        return v != 8
    if b == 4:
        return 2 <= v <= 7
    if b == 5:
        return 4 <= v <= 7
    if b == 6:
        return v == 6 or v == 7
    return False


def banker_pay(stake):
    """A Banker win: 19 for 20, the part chip to the house (DR-059)."""
    return stake * 19 // 20


def settle(side, stake, winner):
    """Net chips for `stake` on `side` when `winner` is PLAYER, BANKER or TIE."""
    if side == TIE:
        return TIE_PAY * stake if winner == TIE else -stake
    if winner == TIE:
        return 0
    if winner != side:
        return -stake
    return banker_pay(stake) if side == BANKER else stake


class Coup:
    """One coup, dealt in full at once so the screen can show it one card at a time: `order` is the
    side each card went to in dealing order (PLAYER, BANKER, PLAYER, BANKER, then any third cards)."""

    def __init__(self, shoe):
        self.player = []
        self.banker = []
        self.order = []
        self.natural = False
        self.winner = None
        self._deal(shoe)

    def _take(self, shoe, side):
        c = shoe.draw()
        (self.player if side == PLAYER else self.banker).append(c)
        self.order.append(side)

    def _deal(self, shoe):
        for side in (PLAYER, BANKER, PLAYER, BANKER):
            self._take(shoe, side)
        p = total(self.player)
        b = total(self.banker)
        if p >= 8 or b >= 8:
            self.natural = True
        else:
            third = None
            if p <= 5:
                self._take(shoe, PLAYER)
                third = points(self.player[2])
            if banker_draws(b, third):
                self._take(shoe, BANKER)
        p = total(self.player)
        b = total(self.banker)
        self.winner = TIE if p == b else (PLAYER if p > b else BANKER)

    def shown(self, n):
        """(player cards, banker cards) after the first n cards of the deal."""
        np = nb = 0
        for side in self.order[:n]:
            if side == PLAYER:
                np += 1
            else:
                nb += 1
        return self.player[:np], self.banker[:nb]

    def totals(self):
        return total(self.player), total(self.banker)
