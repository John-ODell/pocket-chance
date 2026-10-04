# holdem_play_bench.py: Ultimate Hold'em AS BUILT (step 1m), staged in hwtest/stage/, scripted keys.
# Times: deal (full redraw), check->flop (community push + 300 ms pause), check->river (push + pause
# + the outs hint), river raise -> first dealer flip (seats settled before it) -> second flip -> result,
# fold, next, help (holdem_pay import/drop), save; stamps show_band calls to split pushes from pauses.
# Then the same seed with 0 seats to prove the player's result is unchanged. Saves to /_bench_save.*.
import sys, gc, utime, os
sys.path.insert(0, '/remote/stage')
if '/games' not in sys.path: sys.path.append('/games')
from clocks import fast_peripherals; fast_peripherals()
from lcd import LCD
lcd = LCD(62_500_000); gc.collect()
import random
from art import Assets
from save import Store
from bankroll import Bankroll
ASSETS = Assets('/assets')          # like the real program: the 16 KB scratch exists BEFORE the game import
gc.collect(); print("RESULT before_import_holdem mem_free=%d" % gc.mem_free())
import holdem
print("RESULT after_import_holdem mem_free=%d (before gc)" % gc.mem_free()); gc.collect(); print("RESULT after_import_holdem_gc mem_free=%d" % gc.mem_free())
class Keys:
    def poll(self): return []
    def wait_any(self, poll_ms=10): return 'A'
class Ctx: pass
def make(seats, seed):
    ctx = Ctx(); ctx.lcd = lcd; ctx.assets = ASSETS; ctx.buttons = Keys()
    ctx.store = Store('/_bench_save.json'); ctx.rng = random; ctx.bankroll = Bankroll(2000)
    ctx.uth_seats = seats; ctx.uth_hint = True
    random.seed(seed); return holdem.Screen(ctx), ctx
scr, ctx = make(4, 777); t = scr.table
gc.collect(); print("RESULT after_screen_init(4 seats) mem_free=%d" % gc.mem_free())
bands = []; real_band = lcd.show_band
def stamped(y, h): real_band(y, h); bands.append((utime.ticks_us(), y, h))
lcd.show_band = stamped
save_t = []; real_save = ctx.store.save
def tsave(b): t0 = utime.ticks_us(); real_save(b); save_t.append(utime.ticks_diff(utime.ticks_us(), t0))
ctx.store.save = tsave
def press(k):
    bands.clear(); t0 = utime.ticks_us(); scr.handle(k); return t0, utime.ticks_diff(utime.ticks_us(), t0)
deal_t, flop_t, river_t, outs_t, pre_flip, flip_gap, raise_total, fold_t, next_t = [], [], [], [], [], [], [], [], []
scr.draw_all()
for h in range(8):
    t0, dt = press('A'); deal_t.append(dt)                     # deal: full redraw
    t0, dt = press('B'); flop_t.append(dt)                     # check -> flop turns (push + 300 ms)
    t0, dt = press('B'); river_t.append(dt)                    # check -> turn+river (push + 300 ms + outs)
    if t.hint:
        tt = utime.ticks_us(); o = t.round.outs(); outs_t.append(utime.ticks_diff(utime.ticks_us(), tt))
    if h % 2 == 0:
        t0, dt = press('A'); raise_total.append(dt)            # raise 1x: seats settle, two dealer flips, result, save
        dealer = [b for b in bands if b[1] == 24]
        if dealer: pre_flip.append(utime.ticks_diff(dealer[0][0], t0))
        if len(dealer) > 1: flip_gap.append(utime.ticks_diff(dealer[1][0], dealer[0][0]) // 1000)
    else:
        t0, dt = press('B'); fold_t.append(dt)
    t0, dt = press('A'); next_t.append(dt)
def rep(n, xs, u='us'):
    if xs: print("RESULT %s: n=%d mean=%d max=%d %s" % (n, len(xs), sum(xs) // len(xs), max(xs), u))
rep("deal_full_redraw_9_cards_4_seats", deal_t); rep("check_to_flop_handle (push + 300 ms pause)", flop_t)
rep("check_to_river_handle (push + pause + outs hint)", river_t); rep("outs_hint_alone", outs_t)
rep("raise_key_to_first_dealer_flip (seats settled before it)", pre_flip); rep("dealer_flip_gap", flip_gap, 'ms (target 300)')
rep("raise_key_to_result_total", raise_total); rep("fold_to_result", fold_t); rep("next_hand_redraw", next_t)
rep("save_after_hand", save_t)
bal4 = t.bankroll.balance
gc.collect(); m0 = gc.mem_free(); ht = []
for i in range(4):
    t0 = utime.ticks_us(); scr.handle('X'); ht.append(utime.ticks_diff(utime.ticks_us(), t0))
gc.collect(); print("RESULT help_show: n=4 mean_us=%d retained=%d bytes holdem_pay_in_sys_modules=%s" % (sum(ht) // 4, m0 - gc.mem_free(), 'holdem_pay' in sys.modules))
gc.collect(); print("RESULT ram_after_8_hands(4 seats) mem_free=%d balance=%d" % (gc.mem_free(), bal4))
# same seed, no seats: the player's balance must match
lcd.show_band = real_band
scr0, ctx0 = make(0, 777); t0_ = scr0.table; scr0.draw_all()
for h in range(8):
    scr0.handle('A'); scr0.handle('B'); scr0.handle('B'); scr0.handle('A' if h % 2 == 0 else 'B'); scr0.handle('A')
print("RESULT player_result_unaffected_by_seats: balance_4seats=%d balance_0seats=%d same=%s" % (bal4, t0_.bankroll.balance, bal4 == t0_.bankroll.balance))
for p in ('/_bench_save.json', '/_bench_save.bak', '/_bench_save.tmp', '/_bench_save.bad'):
    try: os.remove(p)
    except OSError: pass
gc.collect(); print("RESULT end mem_free=%d cleanup root=%s" % (gc.mem_free(), os.listdir('/')))
