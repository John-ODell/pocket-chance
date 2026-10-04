# pocket_bench.py: plays blackjack hands on the board with SCRIPTED keys (no human), timing every
# redraw path in games/blackjack.py: draw_all (scene change), the top band on a bet change, the
# player band on hit/stand, finish_round (save + draw_all), and the save alone. Uses the real
# lib/ and games/ files on the board, with NO sys.path workaround (HR-F02 is fixed by the rename). Saves go to /_bench_save.* and are removed at the end.
# Run: mpremote connect <port> mount hwtest exec "import pocket_bench"   (needs UPLOAD.md step 1)
import sys, gc, utime
if '/games' not in sys.path:
    sys.path.append('/games')
from clocks import fast_peripherals
print("RESULT clk_peri changed=%s" % fast_peripherals())
from lcd import LCD
lcd = LCD(62_500_000)
gc.collect()
print("RESULT after_lcd mem_free=%d" % gc.mem_free())
import random, os
from art import Assets   # was lib/assets.py; renamed after HR-F02
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

# "time to the banner": stamp the moment draw_all returns, so finish_round can be split into
# key -> banner on screen (what the player feels) and the save that follows (HR-F02 note 2).
_banner_at = [0]
_real_draw_all = scr.draw_all
def _draw_all_stamped():
    _real_draw_all(); _banner_at[0] = utime.ticks_us()
scr.draw_all = _draw_all_stamped
banner_t = []

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
    doubled = False
    while t.state == PLAYING:
        key = 'A' if hand_value(t.round.player)[0] < 17 else 'B'   # hit under 17, else stand
        if not doubled and t.can_double():
            key = 'X'; doubled = True                                # exercise Double once per hand (John: "looked off")
            before_bet, before_bal = t.round.bet, t.bankroll.balance
        t0 = utime.ticks_us()
        scr.handle(key)
        dt = utime.ticks_diff(utime.ticks_us(), t0)
        if key == 'X':
            print("RESULT double: bet %d->%d balance %d->%d cards=%d state=%s outcome=%s" % (before_bet, t.round.bet, before_bal, t.bankroll.balance, len(t.round.player), t.state, getattr(t.round, 'outcome', None)))
        if t.state == RESULT:
            finish_t.append(dt); banner_t.append(utime.ticks_diff(_banner_at[0], t0))
        else:
            play_t.append(dt)
    if t.state == RESULT:
        _, dt = timed('next', scr.handle, 'A'); next_t.append(dt)
    hands += 1
def rep(name, xs, note):
    if xs: print("RESULT %s n=%d mean_us=%d max_us=%d  %s" % (name, len(xs), sum(xs) // len(xs), max(xs), note))
    else: print("RESULT %s n=0" % name)
rep("deal_draw_all", deal_t, "deal -> draw_all (one may include a 700 ms Shuffling pause)")
rep("hit_stand_band", play_t, "draw_player + draw_bottom + show_band 142 rows")
rep("finish_round_total", finish_t, "draw_all + save (atomic, .bak), whole handle() call")
rep("finish_round_key_to_banner", banner_t, "key press -> result banner on screen; the save runs after this")
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
