# Mac-side check of the BACCARAT game as merged (main b102960, step 1q): the real baccarat*.py screen,
# table, seats and rules with stubbed lcd/font/assets/utime. Random keys over long sessions at every
# seat count; a stuck state (300 keys that change nothing) fails; then a rules check against the
# published punto banco edges by simulation, and the drawing positions checked against the 240 px panel.
# Stage first: ./hwtest/stage_from.sh b102960 games/baccarat.py games/baccarat_pay.py games/baccarat_rules.py
#   games/baccarat_seats.py games/baccarat_table.py lib/cards.py lib/bankroll.py
# then: python3 hwtest/bac_fuzz/fuzz.py
import sys, random, collections, types, time
HERE = sys.path[0]
sys.path[:0] = [HERE + '/../stage']

utime = types.ModuleType('utime'); _t = [0]
utime.ticks_us = lambda: _t[0]; utime.ticks_diff = lambda a, b: a - b
SLEEPS = []
def sleep_ms(ms): _t[0] += ms * 1000; SLEEPS.append(ms)
utime.sleep_ms = sleep_ms; sys.modules['utime'] = utime
font = types.ModuleType('font')
DRAWN = []                                   # (x, y, w, h) of every text, to check it fits the panel
def _text(fb, s, x, y, c, size=1): DRAWN.append((x, y, 8 * size * len(s), 8 * size, s))
def _width(s, size=1): return 8 * size * len(s)
font.text = _text; font.width = _width
font.text_centred = lambda fb, s, cx, y, c, size=1: _text(fb, s, cx - _width(s, size) // 2, y, c, size)
font.text_right = lambda fb, s, r, y, c, size=1: _text(fb, s, r - _width(s, size), y, c, size)
sys.modules['font'] = font
pixfmt = types.ModuleType('pixfmt'); pixfmt.rgb = lambda r, g, b: (r << 16) | (g << 8) | b; sys.modules['pixfmt'] = pixfmt
RECTS = []
class LCD:
    def __init__(self): self.shows = 0; self.bands = []
    def fill_rect(self, x, y, w, h, c): RECTS.append((x, y, w, h))
    def __getattr__(self, n): return lambda *a, **k: None
    def show(self): self.shows += 1
    def show_band(self, y, h): self.bands.append((y, h))
class Assets:
    def size(self, n): return None
    def use_sheets(self, s): pass
    def release_sheets(self): pass
    def blit(self, *a): return False
    def background(self, *a): return False
    def background_rows(self, *a): return False
class Buttons:
    def __init__(self): self.q = collections.deque()
    def poll(self):
        out = list(self.q); self.q.clear(); return out
    def wait_any(self, poll_ms=10): return 'A'
class Store:
    def __init__(self): self.saves = 0
    def save(self, b): self.saves += 1
from bankroll import Bankroll
import baccarat
from baccarat_table import BETTING, RESULT, BROKE, MIN_STAKE, MAX_STAKE
from baccarat_rules import Coup, settle, PLAYER, BANKER, TIE, total
from cards import Shoe

KEYS = ('A', 'B', 'X', 'Y', 'UP', 'DOWN', 'LEFT', 'RIGHT', 'PRESS')
def ctx_for(seed, seats, bank):
    return types.SimpleNamespace(lcd=LCD(), assets=Assets(), buttons=Buttons(), store=Store(),
                                 rng=random.Random(seed * 7 + 1), bankroll=Bankroll(bank), bac_seats=seats)
def obs(s):
    t = s.table
    return (t.state, t.bankroll.balance, t.bankroll.bet, t.side, s.shown, None if t.coup is None else id(t.coup))

t0 = time.time(); keys = coups = exits = shuffles = worst = 0; bad = []
for seats in range(6):
    for seed in range(30):
        ctx = ctx_for(seed, seats, 1000 if seed % 3 else 12)
        rng = random.Random(seed); s = baccarat.Screen(ctx); s.draw_all(); last = obs(s); same = 0
        for i in range(4000):
            k = rng.choice(KEYS)
            for _ in range(rng.randrange(3)): ctx.buttons.q.append(rng.choice(KEYS))   # presses during the deal
            before = s.table.state
            if not s.handle(k):
                exits += 1; s = baccarat.Screen(ctx); s.draw_all()
            keys += 1
            t = s.table
            if before in (BETTING, RESULT) and k in ('A',) and t.state == RESULT: coups += 1
            if t.shuffled and t.state == RESULT: shuffles += 1
            assert MIN_STAKE <= t.bankroll.bet <= MAX_STAKE or t.state == BROKE, t.bankroll.bet
            assert t.bankroll.balance >= 0, t.bankroll.balance
            assert len(t.history) <= 12
            assert all(0 <= c <= 10 ** 7 for c in t.seats.chips)
            now = obs(s); same = same + 1 if now == last else 0; last = now; worst = max(worst, same)
            if same >= 300: raise SystemExit('STUCK seats=%d seed=%d state=%s' % (seats, seed, now))
print("RESULT fuzz_ok seats=0..5 x 30 seeds x 4000 keys = %d keys, %d deals, %d exits, %d shuffles seen, longest no-change run %d, %.1fs"
      % (keys, coups, exits, shuffles, worst, time.time() - t0))
print("RESULT max_sleep_ms=%d (300 = card slot, 700 = shuffling)" % max(SLEEPS))
off = [d for d in DRAWN if d[0] < 0 or d[1] < 0 or d[0] + d[2] > 240 or d[1] + d[3] > 240]
print("RESULT texts_drawn=%d off_panel=%d %s" % (len(DRAWN), len(off), sorted(set(o[4] for o in off))[:8]))
offr = [r for r in RECTS if r[0] < 0 or r[1] < 0 or r[0] + r[2] > 240 or r[1] + r[3] > 240]
print("RESULT rects_drawn=%d off_panel=%d" % (len(RECTS), len(offr)))

# rules: simulate the edges (exact values in baccarat_rules.py: Banker 1.06%, Player 1.24%, Tie 14.36%)
rng = random.Random(42); shoe = Shoe(8, rng, penetration=1.0 - 14 / 416.0); N = 400000; w = collections.Counter(); net = [0, 0, 0]
for _ in range(N):
    if shoe.needs_shuffle(): shoe.shuffle()
    c = Coup(shoe); w[c.winner] += 1
    for side in (PLAYER, BANKER, TIE): net[side] += settle(side, 20, c.winner)     # stake 20: 19 for 20 exact
print("RESULT sim %d coups: Player %.2f%% Banker %.2f%% Tie %.2f%% (published 44.6 / 45.9 / 9.5)" % (N, *(100.0 * w[s] / N for s in (PLAYER, BANKER, TIE))))
print("RESULT edge at stake 20: Player %.2f%% Banker %.2f%% Tie %.2f%% (published 1.24 / 1.06 / 14.36)" % tuple(-100.0 * n / (20 * N) for n in net))
print("RESULT banker pay at stake 5 = %d (DR-059: 19//20 rounds the part chip to the house)" % settle(BANKER, 5, BANKER))

# long session: one table, 1000 coups straight (several shoes), side and stake changed between coups
SLEEPS.clear(); ctx = ctx_for(3, 5, 1000); s = baccarat.Screen(ctx); s.draw_all(); rng = random.Random(3)
shuf = 0; deals = 0; seen_hist = 0
for i in range(1000):
    k = rng.choice(('A', 'A', 'A', 'LEFT', 'RIGHT', 'UP', 'DOWN'))
    if s.table.state == BROKE: k = 'A'
    st0 = s.table.state; assert s.handle(k)
    if s.table.state == RESULT and st0 != RESULT or (st0 == RESULT and k == 'A'):
        deals += 1; shuf += s.table.shuffled
    seen_hist = max(seen_hist, len(s.table.history))
print("RESULT long_session: %d keys, %d deals, %d shuffles ('Shuffling...' 700 ms shown %d times), history kept %d, balance %d, seat chips %s"
      % (1000, deals, shuf, SLEEPS.count(700), seen_hist, s.table.bankroll.balance, s.table.seats.chips))
