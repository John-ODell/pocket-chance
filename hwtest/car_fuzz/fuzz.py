# Mac-side fuzz of the installed Caribbean game (e8244ec): the real caribbean.py Screen and table
# with stubbed lcd/font/assets/utime, random keys incl. unhandled ones, every seat count, long runs.
# A "freeze" here = a state in which many consecutive keys change nothing observable.
import sys, random, collections, types, time
HERE = sys.path[0]
sys.path[:0] = [HERE + '/../stage']        # stage games/caribbean*.py AND lib/poker.py cards.py bankroll.py first

# ---- stubs ---------------------------------------------------------------------------------------
utime = types.ModuleType('utime'); _t = [0]
utime.ticks_us = lambda: _t[0]; utime.ticks_diff = lambda a, b: a - b
def sleep_ms(ms): _t[0] += ms * 1000; SLEEPS.append(ms)
utime.sleep_ms = sleep_ms; sys.modules['utime'] = utime
SLEEPS = []
font = types.ModuleType('font')
for n in ('text', 'text_centred', 'text_right'): setattr(font, n, lambda *a, **k: None)
sys.modules['font'] = font
pixfmt = types.ModuleType('pixfmt'); pixfmt.rgb = lambda r, g, b: (r << 16) | (g << 8) | b; sys.modules['pixfmt'] = pixfmt
class LCD:
    def __init__(self): self.shows = 0; self.bands = []
    def __getattr__(self, n): return lambda *a, **k: None       # fill_rect, hline, vline, rect, ellipse, fill
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
    def __init__(self): self.q = collections.deque(); self.drained = 0
    def poll(self):
        out = list(self.q); self.drained += len(out); self.q.clear(); return out
    def wait_any(self, poll_ms=10): return 'A'
class Store:
    def __init__(self): self.saves = 0
    def save(self, b): self.saves += 1
from bankroll import Bankroll
import caribbean
from caribbean_table import BETTING, DECIDING, RESULT, BROKE

KEYS = ('A', 'B', 'X', 'Y', 'UP', 'DOWN', 'LEFT', 'RIGHT', 'PRESS')
def obs(scr):
    t = scr.table; r = t.round
    return (t.state, t.bankroll.balance, t.bankroll.bet, scr.board_shown, scr.dealer_shown, t.armed,
            None if r is None else (r.state, r.outcome))

def run(seed, seats, steps, start=1000, in_game_keys=False):
    rng = random.Random(seed)
    ctx = types.SimpleNamespace(lcd=LCD(), assets=Assets(), buttons=Buttons(), store=Store(),
                                rng=random.Random(seed * 7 + 1), bankroll=Bankroll(start), car_seats=seats)
    scr = caribbean.Screen(ctx)
    scr.draw_all()
    stats = collections.Counter(); same = 0; worst_same = 0; x3 = 0; broke = 0; helps = 0
    last = obs(scr)
    for i in range(steps):
        k = rng.choice(KEYS)
        if in_game_keys:                              # presses "during the delays": queued before handle
            for _ in range(rng.randrange(3)): ctx.buttons.q.append(rng.choice(KEYS))
        stats[(scr.table.state, k)] += 1
        if k == 'X': helps += 1
        alive = scr.handle(k)
        if not alive:
            # left the game: re-enter exactly like pocket.play() does (a new Screen)
            stats['exit'] += 1
            scr = caribbean.Screen(ctx); scr.draw_all()
        now = obs(scr)
        if now == last: same += 1; worst_same = max(worst_same, same)
        else: same = 0
        last = now
        t = scr.table
        if t.state == RESULT and t.round.mult > 1: x3 += 1
        if t.state == BROKE: broke += 1
        if same >= 300:
            raise SystemExit('FREEZE seed=%d seats=%d step=%d state=%s' % (seed, seats, i, now))
    return stats, worst_same, x3, broke, helps, ctx

t0 = time.time(); total_x3 = 0; total_exit = 0; worst = 0; hands = 0
for seats in (0, 1, 2, 3, 4):
    for seed in range(40):
        stats, ws, x3, broke, helps, ctx = run(seed, seats, 4000, start=(1000 if seed % 4 else 30),
                                           in_game_keys=bool(seed % 2))
        total_x3 += x3; total_exit += stats['exit']; worst = max(worst, ws)
        hands += sum(v for (st_k, v) in stats.items() if isinstance(st_k, tuple) and st_k == (DECIDING, 'A'))
print("RESULT fuzz_ok seats=0..4 seeds=40 steps=4000 each (800k keys) in %.1fs" % (time.time() - t0))
print("RESULT high_calls=%d x3_results=%d exits=%d worst_no_change_run=%d" % (hands, total_x3, total_exit, worst))
print("RESULT max_sleep_ms=%d" % max(SLEEPS))
# targeted: help from every state, keys queued during deal/showdown, broke/refill, x3 hand then more
ctx = types.SimpleNamespace(lcd=LCD(), assets=Assets(), buttons=Buttons(), store=Store(),
                            rng=random.Random(5), bankroll=Bankroll(1000), car_seats=4)
scr = caribbean.Screen(ctx); scr.draw_all()
for st_keys in (('X',), ('A', 'X'), ('A', 'A', 'X'), ('A', 'Y', 'X'), ('A', 'B', 'X')):
    s2 = caribbean.Screen(ctx); s2.draw_all()
    for k in st_keys: assert s2.handle(k)
    assert s2.table.state in (BETTING, DECIDING, RESULT), s2.table.state
print("RESULT help_from_betting_deciding_result_ok")
scr = caribbean.Screen(types.SimpleNamespace(lcd=LCD(), assets=Assets(), buttons=Buttons(), store=Store(),
                                             rng=random.Random(9), bankroll=Bankroll(20), car_seats=4))
assert scr.table.state == BROKE; assert scr.handle('X') and scr.table.state == BROKE
assert scr.handle('A') and scr.table.state == BETTING and scr.table.bankroll.balance == 1000
print("RESULT broke_refill_ok (X ignored when broke, A refills)")
# chase an x3 hand and play 50 more after it
n = 0; seen = 0
while seen < 20 and n < 200000:
    n += 1
    scr.handle('A'); scr.handle('A')                       # deal (or refill when broke), then high call
    r = scr.table.round
    if r is not None and r.mult > 1: seen += 1
    scr.handle('A')
print("RESULT x3_hands_played=%d in %d hands, state after=%s" % (seen, n, scr.table.state))
