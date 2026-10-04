# stud_play_bench.py: Caribbean Stud AS BUILT (step 1j), staged from hwtest/stage/, scripted keys.
# Times: deal (10-card full redraw), each reveal flip and its spacing, key-to-result, fold, next,
# paytable (stud_pay import/drop retention over 5 shows), save; code-drawn then with a temp cards
# sheet. Saves go to /_bench_save.*. Leaves the board's files untouched.
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
import stud
from stud_table import BETTING, DECIDING, RESULT, BROKE
gc.collect(); print("RESULT after_imports mem_free=%d" % gc.mem_free())
class Keys:
    def poll(self): return []
    def wait_any(self, poll_ms=10): return 'A'
class Ctx: pass
ctx = Ctx(); ctx.lcd = lcd; ctx.assets = Assets('/assets'); ctx.buttons = Keys()
ctx.store = Store('/_bench_save.json'); ctx.rng = random; ctx.bankroll = Bankroll(2000)
random.seed(31337)
scr = stud.Screen(ctx); t = scr.table
gc.collect(); print("RESULT after_screen_init mem_free=%d" % gc.mem_free())
bands = []; real_band = lcd.show_band
def stamped_band(y, h): real_band(y, h); bands.append((utime.ticks_us(), y, h))
lcd.show_band = stamped_band
save_t = []; real_save = ctx.store.save
def timed_save(b): t0 = utime.ticks_us(); real_save(b); save_t.append(utime.ticks_diff(utime.ticks_us(), t0))
ctx.store.save = timed_save
def press(k):
    t0 = utime.ticks_us(); scr.handle(k); return utime.ticks_diff(utime.ticks_us(), t0)
def run(label):
    deal_t, raise_total, fold_t, next_t, gaps, flips = [], [], [], [], [], []
    scr.draw_all()
    for h in range(6):
        deal_t.append(press('A'))
        if t.state != DECIDING:
            continue
        bands.clear(); t0 = utime.ticks_us()
        if h % 2 == 0:
            raise_total.append(press('A'))
            stamps = [b for b in bands if b[2] == 72]          # the dealer-band pushes = flips
            for i in range(1, len(stamps)): gaps.append(utime.ticks_diff(stamps[i][0], stamps[i-1][0]) // 1000)
            flips.append(len(stamps))
        else:
            fold_t.append(press('B'))
        if t.state == RESULT: next_t.append(press('A'))
    def rep(n, xs, unit='us'):
        if xs: print("RESULT %s %s: n=%d mean=%d max=%d %s" % (label, n, len(xs), sum(xs) // len(xs), max(xs), unit))
    rep("deal_full_redraw_10_cards", deal_t); rep("raise_key_to_result_total", raise_total)
    rep("reveal_flip_spacing", gaps, 'ms (target 300)'); rep("fold_to_result", fold_t); rep("next_hand_redraw", next_t)
    print("RESULT %s dealer_band_pushes_per_raise=%s" % (label, flips))
run("code_drawn")
rep_save = save_t[:]
# paytable: stud_pay imported and dropped per show?
gc.collect(); m0 = gc.mem_free(); pt = []
for i in range(5):
    t0 = utime.ticks_us(); scr.handle('X'); pt.append(utime.ticks_diff(utime.ticks_us(), t0))
gc.collect(); print("RESULT paytable_show: n=5 mean_us=%d max_us=%d retained_after_5_shows=%d bytes stud_pay_in_sys_modules=%s" % (sum(pt) // 5, max(pt), m0 - gc.mem_free(), 'stud_pay' in sys.modules))
if save_t: print("RESULT save_after_hand: n=%d mean_us=%d max_us=%d" % (len(save_t), sum(save_t) // len(save_t), max(save_t)))
gc.collect(); print("RESULT ram_after_code_drawn mem_free=%d balance=%d" % (gc.mem_free(), t.bankroll.balance))
W, H, N = 40, 56, 53
try:
    with open('/assets/cards.565', 'wb') as f:
        f.write(bytes([W & 255, W >> 8, (H * N) & 255, (H * N) >> 8])); r = bytes([0x12, 0x34]) * W
        for k in range(N):
            for y in range(H): f.write(r)
    ctx.assets.missing.clear(); ctx.assets.known.clear()
    if hasattr(ctx.assets, 'use_sheets'): ctx.assets.use_sheets(('cards',))
    print("RESULT sheet_open=%s" % (list(getattr(ctx.assets, 'open_sheets', {}).keys()),))
    run("sheet_cards")
    if hasattr(ctx.assets, 'release_sheets'): ctx.assets.release_sheets()
finally:
    try: os.remove('/assets/cards.565')
    except OSError: pass
gc.collect(); print("RESULT end mem_free=%d" % gc.mem_free())
for p in ('/_bench_save.json', '/_bench_save.bak', '/_bench_save.tmp', '/_bench_save.bad'):
    try: os.remove(p)
    except OSError: pass
print("RESULT cleanup root=%s assets=%s" % (os.listdir('/'), os.listdir('/assets')))
