# pocket_bench.py: plays blackjack hands on the board with SCRIPTED keys (no human), timing every
# redraw path in games/blackjack.py: draw_all (scene change), the top band on a bet change, the
# player band on hit/stand, finish_round (save + draw_all), and the save alone. Uses the real
# lib/ and games/ files on the board. Saves go to /_bench_save.* and are removed at the end.
# Run: mpremote connect <port> mount hwtest exec "import pocket_bench"   (needs UPLOAD.md step 1)
import sys, gc, utime
if '/games' not in sys.path:
    sys.path.append('/games')
# WORKAROUND for finding F02: the /assets folder shadows lib/assets.py because '' precedes /lib on
# sys.path and MicroPython 1.29 treats a bare directory as a package. Putting /lib first proves it.
sys.path.insert(0, '/lib')
from clocks import fast_peripherals
print("RESULT clk_peri changed=%s" % fast_peripherals())
from lcd import LCD
lcd = LCD(62_500_000)
gc.collect()
print("RESULT after_lcd mem_free=%d" % gc.mem_free())
import random, os
from assets import Assets
from save import Store
from bankroll import Bankroll
from cards import hand_value
import blackjack
from blackjack_table import BETTING, PLAYING, RESULT, BROKE
gc.collect()
print("RESULT after_all_imports mem_free=%d" % gc.mem_free())

class Keys:
    def poll(self): return []

class Ctx: pass
ctx = Ctx()
ctx.lcd = lcd; ctx.assets = Assets('/assets'); ctx.buttons = Keys()
ctx.store = Store('/_bench_save.json'); ctx.rng = random; ctx.bankroll = Bankroll()
random.seed(12345)
scr = blackjack.Screen(ctx)
t = scr.table

def timed(label, fn, *a):
    t0 = utime.ticks_us(); r = fn(*a); return r, utime.ticks_diff(utime.ticks_us(), t0)

_, dt = timed('draw_all', scr.draw_all)
print("RESULT draw_all_us=%d (full redraw + show, code-drawn felt)" % dt)
bet_t = []
for k in ('UP', 'UP', 'RIGHT', 'DOWN'):
    _, dt = timed(k, scr.handle, k); bet_t.append(dt)
print("RESULT bet_change_band_us mean=%d max=%d (draw_top + show_band 24 rows)" % (sum(bet_t) // 4, max(bet_t)))
deal_t, play_t, finish_t, next_t = [], [], [], []
hands = 0
while hands < 8 and t.state != BROKE:
    _, dt = timed('deal', scr.handle, 'A')
    (finish_t if t.state == RESULT else deal_t).append(dt)   # deal that ends at once = finish path
    while t.state == PLAYING:
        key = 'A' if hand_value(t.round.player)[0] < 17 else 'B'   # hit under 17, else stand
        _, dt = timed(key, scr.handle, key)
        (finish_t if t.state == RESULT else play_t).append(dt)
    if t.state == RESULT:
        _, dt = timed('next', scr.handle, 'A'); next_t.append(dt)
    hands += 1
def rep(name, xs, note):
    if xs: print("RESULT %s n=%d mean_us=%d max_us=%d  %s" % (name, len(xs), sum(xs) // len(xs), max(xs), note))
    else: print("RESULT %s n=0" % name)
rep("deal_draw_all", deal_t, "deal -> draw_all (one may include a 700 ms Shuffling pause)")
rep("hit_stand_band", play_t, "draw_player + draw_bottom + show_band 142 rows")
rep("finish_round", finish_t, "save (atomic, .bak) + draw_all")
rep("next_hand_draw_all", next_t, "draw_all")
sv = []
for i in range(5):
    _, dt = timed('save', ctx.store.save, 1000 + i); sv.append(dt)
rep("save_alone", sv, "write tmp, rename old->bak, rename tmp->json")
gc.collect()
print("RESULT end mem_free=%d hands=%d balance=%d" % (gc.mem_free(), hands, t.bankroll.balance))
for p in ('/_bench_save.json', '/_bench_save.bak', '/_bench_save.tmp', '/_bench_save.bad'):
    try: os.remove(p)
    except OSError: pass
print("RESULT cleanup root=%s" % os.listdir('/'))
lcd.fill(0); lcd.show()
