# Slots session logic: approved configuration (DR-017, DR-018), bet limits (DR-019), the spin
# animation plan (DR-020 motion) and the bankroll flow. Pure logic: no `machine` import.

from slots_rules import strip, Paytable, Reels, CHERRY, LEMON, ORANGE, BELL, BAR, SEVEN, DIAMOND, STAR

# DR-017: identical 32-stop strips.  DR-018: paytable A, RTP 93.84%, 1000x jackpot.
COUNTS = {CHERRY: 3, LEMON: 7, ORANGE: 6, BELL: 5, BAR: 4, SEVEN: 3, DIAMOND: 3, STAR: 1}
THREE = {STAR: 1000, DIAMOND: 200, SEVEN: 100, BAR: 40, BELL: 20, ORANGE: 14, LEMON: 10, CHERRY: 8}
CHERRIES = {2: 3, 1: 1}
# DR-019: bets 5 to 100 per spin in steps of 5, shared bankroll.
MIN_BET, MAX_BET, STEP = 5, 100, 5

BETTING = 'betting'
RESULT = 'result'
BROKE = 'broke'

SYM_PX = 56          # window and symbol height
FAST = 8             # px per frame at full speed (one symbol every 7 frames)
SLOW = 2             # px per frame over the last symbol
BASE_SYMBOLS = 10    # symbols the left reel travels at full speed
EXTRA_PER_REEL = 3   # more symbols per reel to the right: stops about 0.4 s apart at 50 fps
START_LAG = 2        # frames between reel starts, so symbol changes never share a frame (HR-020)


def default_paytable():
    return Paytable(three=THREE, cherries=CHERRIES)


def default_reels(rng):
    return Reels([strip(COUNTS)] * 3, default_paytable(), rng)


class SpinPlan:
    """Frame-by-frame reel positions for one spin, ending exactly on `stops`.

    Each reel travels a fixed distance: (BASE_SYMBOLS + EXTRA_PER_REEL * i + 1) symbols, the last
    one at SLOW px per frame, then snaps. The reel is repositioned so that distance ends on its
    stop (the jump is invisible: the reel is moving 8 px a frame from the first frame).
    After step(): top[i] is the strip index shown at the top of window i, off[i] its upward pixel
    offset (0..55; the next strip symbol shows below it), changed[i] is True on the frame the top
    symbol advanced (the screen loads the following symbol then), done when all reels rest.
    """

    def __init__(self, strip_len, stops, base=BASE_SYMBOLS, extra=EXTRA_PER_REEL, lag=START_LAG):
        n = len(stops)
        self.strip_len = strip_len
        self.stops = list(stops)
        self.total = [(base + extra * i + 1) * SYM_PX for i in range(n)]
        self.start = [(stops[i] - self.total[i] // SYM_PX) % strip_len for i in range(n)]
        self.lag = [lag * i for i in range(n)]
        self.pos = [0] * n
        self.frame = 0
        self.top = list(self.start)
        self.off = [0] * n
        self.changed = [False] * n
        self.done = False

    def moving(self, i):
        return self.pos[i] < self.total[i]

    def step(self):
        """Advance one frame. Returns self.done."""
        self.frame += 1
        all_done = True
        for i in range(len(self.pos)):
            self.changed[i] = False
            if self.frame <= self.lag[i] or self.pos[i] >= self.total[i]:
                if self.pos[i] < self.total[i]:
                    all_done = False
                continue
            remaining = self.total[i] - self.pos[i]
            speed = FAST if remaining > SYM_PX else SLOW
            if speed > remaining:
                speed = remaining
            old_top = self.pos[i] // SYM_PX
            self.pos[i] += speed
            new_top = self.pos[i] // SYM_PX
            self.top[i] = (self.start[i] + new_top) % self.strip_len
            self.off[i] = self.pos[i] % SYM_PX
            self.changed[i] = new_top != old_top
            if self.pos[i] < self.total[i]:
                all_done = False
        self.done = all_done
        return self.done


class SlotsTable:
    def __init__(self, rng, bankroll, reels=None):
        self.bankroll = bankroll
        self.reels = reels or default_reels(rng)
        self.last = None              # (win, label) of the last spin
        self._fit_bet()
        self.state = BROKE if self.bankroll.balance < MIN_BET else BETTING

    def _fit_bet(self):
        b = self.bankroll
        top = min(MAX_BET, b.balance)
        top -= top % STEP
        if b.bet > top:
            b.bet = top
        if b.bet < MIN_BET:
            b.bet = MIN_BET

    def adjust_bet(self, delta):
        if self.state != BETTING:
            raise ValueError('not betting')
        self.bankroll.bet += delta
        self._fit_bet()
        return self.bankroll.bet

    def spin(self):
        """Take the bet, pick the stops. Returns (win, label); the screen animates to reels.stops."""
        if self.state != BETTING:
            raise ValueError('not betting')
        self._fit_bet()
        bet = self.bankroll.bet
        win, label = self.reels.spin(bet)
        self.bankroll.apply(win - bet)
        self.last = (win, label)
        self.state = RESULT
        return win, label

    def plan(self):
        """SpinPlan for the stops just chosen."""
        return SpinPlan(len(self.reels.strips[0]), self.reels.stops)

    def next(self):
        if self.state != RESULT:
            raise ValueError('no result to leave')
        self.state = BROKE if self.bankroll.balance < MIN_BET else BETTING
        self._fit_bet()

    def refill(self):
        if self.state != BROKE:
            raise ValueError('not broke')
        self.bankroll.refill()
        self._fit_bet()
        self.state = BETTING

    def stakes(self):
        return self.bankroll.balance, self.bankroll.bet

    def paytable_rows(self, bet):
        """[(label, pay)] for the paytable screen at this bet, best first."""
        pt = self.reels.paytable
        from slots_rules import SYMBOLS
        rows = [('3 x ' + SYMBOLS[s], pay * bet) for s, pay in sorted(pt.three.items(), key=lambda kv: -kv[1])]
        for n in sorted(pt.cherries, reverse=True):
            rows.append(('%d cherr%s' % (n, 'y' if n == 1 else 'ies'), pt.cherries[n] * bet))
        return rows
