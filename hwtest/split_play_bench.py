# split_play_bench.py: DR-016 as BUILT (step 1c). Scripted keys, no human. Deals until a pair turns
# up, presses Y, plays both hands (double once if allowed, hit under 17, else stand), times every
# redraw and key->banner. Then rigs a hand of two aces and splits it (one card each, round ends).
# Saves go to /_bench_save.* and are removed. Run: mpremote connect <port> mount hwtest exec "import split_play_bench"
import sys, gc, utime, os
if '/games' not in sys.path:
    sys.path.append('/games')
from clocks import fast_peripherals
fast_peripherals()
from lcd import LCD
lcd = LCD(62_500_000); gc.collect()
import random
from art import Assets
from save import Store
from bankroll import Bankroll
from cards import hand_value, card_name
import blackjack
from blackjack_table import BETTING, PLAYING, RESULT, BROKE
gc.collect(); print("RESULT after_imports mem_free=%d" % gc.mem_free())

class Keys:
    def poll(self): return []
class Ctx: pass
ctx = Ctx(); ctx.lcd = lcd; ctx.assets = Assets('/assets'); ctx.buttons = Keys()
ctx.store = Store('/_bench_save.json'); ctx.rng = random; ctx.bankroll = Bankroll(5000)
random.seed(777)
scr = blackjack.Screen(ctx); t = scr.table
banner_at = [0]; real_draw_all = scr.draw_all
def stamped(): real_draw_all(); banner_at[0] = utime.ticks_us()
scr.draw_all = stamped
scr.draw_all()

def press(key):
    t0 = utime.ticks_us(); scr.handle(key); dt = utime.ticks_diff(utime.ticks_us(), t0)
    return dt, (utime.ticks_diff(banner_at[0], t0) if t.state == RESULT else None)

def play_out(times, banners, doubled_once):
    while t.state == PLAYING:
        r = t.round
        if not doubled_once[0] and t.can_double():
            key = 'X'; doubled_once[0] = True
        else:
            key = 'A' if hand_value(r.hands[r.active])[0] < 17 else 'B'
        dt, b = press(key); times.append((key, dt))
        if b is not None: banners.append(b)

splits = 0; deals = 0; split_t = []; play_t = []; banners = []; errors = 0
while splits < 3 and deals < 400 and t.state != BROKE:
    if t.state == RESULT: press('A')
    dt, b = press('A'); deals += 1
    if t.state == PLAYING and t.can_split():
        bet0, bal0 = t.round.bet, t.bankroll.balance
        dt, b = press('Y'); split_t.append(dt); splits += 1
        r = t.round
        print("RESULT split#%d after %d deals: hands=%s bets=%s stake %d->%d is_split=%s active=%d state=%s split_redraw_us=%d" %
              (splits, deals, [[card_name(c) for c in h] for h in r.hands], r.bets, bet0, r.bet, r.is_split, r.active, t.state, dt))
        play_out(play_t, banners, [False])
        if t.state == RESULT:
            print("RESULT split#%d result: hands=%s outcomes=%s net=%d balance=%d" %
                  (splits, [[card_name(c) for c in h] for h in r.hands], getattr(r, 'outcomes', getattr(r, 'outcome', None)), r.net, t.bankroll.balance))
    else:
        play_out([], [], [True])
print("RESULT natural_splits=%d in %d deals" % (splits, deals))
if split_t: print("RESULT press_Y_redraw_us mean=%d max=%d" % (sum(split_t) // len(split_t), max(split_t)))
if play_t:
    for k in ('A', 'B', 'X'):
        xs = [d for kk, d in play_t if kk == k]
        if xs: print("RESULT split_play key=%s n=%d mean_us=%d max_us=%d" % (k, len(xs), sum(xs) // len(xs), max(xs)))
if banners: print("RESULT split_key_to_banner n=%d mean_us=%d max_us=%d" % (len(banners), sum(banners) // len(banners), max(banners)))

# rigged aces: deal, then replace the player's cards with two aces and split
try:
    if t.state == RESULT: press('A')
    press('A')
    aces = [c for c in range(52) if card_name(c)[0] == 'A'][:2]
    if len(aces) == 2 and t.state == PLAYING:
        t.round.hands[0] = list(aces)
        if t.can_split():
            dt, b = press('Y'); r = t.round
            print("RESULT aces: hands=%s state=%s (expect 2 cards each, round over) key_to_banner_us=%s redraw_us=%d" %
                  ([[card_name(c) for c in h] for h in r.hands], t.state, b, dt))
        else:
            print("RESULT aces: can_split False after rig; cards=%s" % [card_name(c) for c in t.round.hands[0]])
    else:
        print("RESULT aces: skipped (card codes not 0..51 or not playing)")
except Exception as e:
    print("RESULT aces: ERROR %r" % (e,))
gc.collect(); print("RESULT end mem_free=%d" % gc.mem_free())
for p in ('/_bench_save.json', '/_bench_save.bak', '/_bench_save.tmp', '/_bench_save.bad'):
    try: os.remove(p)
    except OSError: pass
print("RESULT cleanup root=%s" % os.listdir('/'))
lcd.fill(0); lcd.show()
