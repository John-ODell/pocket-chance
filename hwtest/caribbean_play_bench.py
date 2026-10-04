# caribbean_play_bench.py: the Caribbean flop game AS BUILT (branch flop-game, DR-062..069), staged in
# hwtest/stage/, scripted keys, run from the mount only. Times: deal (full redraw + 300 ms + flop band
# + bottom band), call high / call low / fold -> showdown (turn+river band, 300 ms, dealer flip 1, 300 ms,
# full result redraw, save), next hand, help (caribbean_pay import/drop); RAM before/after import, after
# screen init, after each hand (leak check); the deal-to-flop gap and the dealer flip gap from stamped
# show_band calls. Then the same seed with 0 seats to prove the player's result is unchanged.
# Saves go to /_bench_save.*; John's /save.json is not touched. clocks.py is a tripwire in the stage.
import sys, gc, utime, os
sys.path.insert(0, '/remote/stage')
if '/games' not in sys.path: sys.path.append('/games')
import machine
machine.freq(125_000_000, 125_000_000)           # DR-050
from lcd import LCD
lcd = LCD(62_500_000); gc.collect()
import random
from art import Assets
from save import Store
from bankroll import Bankroll
ASSETS = Assets('/assets')
gc.collect(); print("RESULT before_import_caribbean mem_free=%d" % gc.mem_free())
import caribbean
print("RESULT after_import_caribbean mem_free=%d (before gc)" % gc.mem_free()); gc.collect()
print("RESULT after_import_caribbean_gc mem_free=%d" % gc.mem_free())
print("RESULT caribbean_from=%s" % caribbean.__file__)
class Keys:
    def poll(self): return []
    def wait_any(self, poll_ms=10): return 'A'
class Ctx: pass
def make(seats, seed):
    ctx = Ctx(); ctx.lcd = lcd; ctx.assets = ASSETS; ctx.buttons = Keys()
    ctx.store = Store('/_bench_save.json'); ctx.rng = random; ctx.bankroll = Bankroll(2000)
    ctx.car_seats = seats
    random.seed(seed); return caribbean.Screen(ctx), ctx
scr, ctx = make(4, 777); t = scr.table
gc.collect(); print("RESULT after_screen_init(4 seats) mem_free=%d" % gc.mem_free())
bands = []; real_band = lcd.show_band
def stamped(y, h): real_band(y, h); bands.append((utime.ticks_us(), y, h))
lcd.show_band = stamped
shows = []; real_show = lcd.show
def tshow(): t0 = utime.ticks_us(); real_show(); shows.append(utime.ticks_diff(utime.ticks_us(), t0))
lcd.show = tshow
save_t = []; real_save = ctx.store.save
def tsave(b): t0 = utime.ticks_us(); real_save(b); save_t.append(utime.ticks_diff(utime.ticks_us(), t0))
ctx.store.save = tsave
def press(k):
    bands.clear(); shows.clear(); t0 = utime.ticks_us(); scr.handle(k); return t0, utime.ticks_diff(utime.ticks_us(), t0)
deal_t, deal_draw, flop_gap, flop_band, bottom_band = [], [], [], [], []
show_t, dealer_gap, river_gap, total_t, next_t, mem = {}, [], [], {}, [], []
outcomes = []
scr.draw_all()
for h in range(12):
    t0, dt = press('A'); deal_t.append(dt)                       # deal: full redraw, pause, flop band, bottom band
    if shows: deal_draw.append(shows[0])
    comm = [b for b in bands if b[1] == 84]; bot = [b for b in bands if b[1] == 204]
    if comm: flop_gap.append(utime.ticks_diff(comm[0][0], t0) // 1000)
    k = ('A', 'Y', 'B')[h % 3]
    t0, dt = press(k); total_t.setdefault(k, []).append(dt)       # showdown: river band, flip, result redraw, save
    comm = [b for b in bands if b[1] == 84]; dl = [b for b in bands if b[1] == 24]
    if comm and dl: river_gap.append(utime.ticks_diff(dl[0][0], comm[0][0]) // 1000)
    if dl: dealer_gap.append(utime.ticks_diff(t0 + dt, dl[0][0]) // 1000)   # flip 1 -> end (incl. result redraw+save)
    if shows: show_t.setdefault(k, []).append(shows[-1])
    outcomes.append((t.round.outcome, t.round.net, t.round.mult))
    t0, dt = press('A'); next_t.append(dt)                       # next hand
    gc.collect(); mem.append(gc.mem_free())
def rep(n, xs, u='us'):
    if xs: print("RESULT %s: n=%d mean=%d max=%d %s" % (n, len(xs), sum(xs) // len(xs), max(xs), u))
rep("deal_handle_total (redraw + 300 ms + flop band + bottom band)", deal_t)
rep("deal_full_redraw_show", deal_draw); rep("deal_key_to_flop_band", flop_gap, 'ms (target >= 300)')
for k in ('A', 'Y', 'B'):
    rep("showdown_total_%s (river band, 300, flip, 300, result redraw, save)" % k, total_t.get(k, []))
    rep("result_redraw_show_%s" % k, show_t.get(k, []))
rep("river_band_to_dealer_flip_gap", river_gap, 'ms (target 300)')
rep("dealer_flip_to_result_end", dealer_gap, 'ms (300 pause + redraw + save)')
rep("next_hand_redraw", next_t); rep("save", save_t)
print("RESULT mem_free_after_each_hand=%s" % mem)
print("RESULT outcomes=%s" % outcomes)
print("RESULT bankroll_4_seats=%d armed=%s" % (ctx.bankroll.balance, t.armed))
# help screen: import and drop
gc.collect(); m0 = gc.mem_free(); t0 = utime.ticks_us(); scr.help(); dt = utime.ticks_diff(utime.ticks_us(), t0)
gc.collect(); print("RESULT help_total_us=%d mem_before=%d mem_after=%d caribbean_pay_loaded=%s" % (dt, m0, gc.mem_free(), 'caribbean_pay' in sys.modules))
# same seed, 0 seats: the player's cards and result must be identical
lcd.show_band = real_band; lcd.show = real_show
scr0, ctx0 = make(0, 777); t0_ = scr0.table; out0 = []
for h in range(12):
    scr0.handle('A'); scr0.handle(('A', 'Y', 'B')[h % 3]); out0.append((t0_.round.outcome, t0_.round.net, t0_.round.mult)); scr0.handle('A')
print("RESULT bankroll_0_seats=%d" % ctx0.bankroll.balance)
print("RESULT identical_player_result_0_vs_4_seats=%s" % (out0 == [(o, n, 1) for (o, n, m) in outcomes] or out0 == outcomes))
print("RESULT outcomes_0_seats=%s" % out0)
for f in ('/_bench_save.json', '/_bench_save.bak'):
    try: os.remove(f)
    except OSError: pass
gc.collect(); print("RESULT end mem_free=%d" % gc.mem_free())
