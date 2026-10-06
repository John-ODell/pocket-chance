# baccarat_play_bench.py: the BACCARAT game AS MERGED (main b102960, UPLOAD.md step 1q), staged in
# hwtest/stage/, run from the mount only. Times: the deal (Shuffling band when it happens, the full
# redraw, each card's 72-row band push inside its 300 ms slot, the result redraw, the save), a joystick
# move in betting (top band + bottom band), the pays screen (baccarat_pay import and drop), the 8-deck
# shuffle itself; RAM before/after import, after screen init, after every 10 coups over 250 coups
# (three shoes: leak check). Saves go to /_bench_save.*; John's /save.json is not touched.
# clocks.py in the stage is a tripwire.
import sys, gc, utime, os
sys.path.insert(0, '/remote/stage')
if '/games' not in sys.path: sys.path.append('/games')
import machine
machine.freq(125_000_000, 125_000_000)           # DR-050, what pocket.py does at boot
from lcd import LCD
lcd = LCD(62_500_000); gc.collect()
import random
from art import Assets
from save import Store
from bankroll import Bankroll
ASSETS = Assets('/assets')
gc.collect(); print("RESULT before_import_baccarat mem_free=%d" % gc.mem_free())
import baccarat
print("RESULT after_import_baccarat mem_free=%d (before gc)" % gc.mem_free()); gc.collect()
print("RESULT after_import_baccarat_gc mem_free=%d" % gc.mem_free())
print("RESULT baccarat_from=%s" % baccarat.__file__)
class Keys:
    def poll(self): return []
    def wait_any(self, poll_ms=10): return 'A'
class Ctx: pass
ctx = Ctx(); ctx.lcd = lcd; ctx.assets = ASSETS; ctx.buttons = Keys()
ctx.store = Store('/_bench_save.json'); ctx.rng = random; ctx.bankroll = Bankroll(1000); ctx.bac_seats = 5
random.seed(777)
scr = baccarat.Screen(ctx); t = scr.table
gc.collect(); print("RESULT after_screen_init(5 seats) mem_free=%d" % gc.mem_free())

# 8-deck shuffle on its own (Shoe.shuffle: 416 Fisher-Yates swaps, one bytearray)
ts = []
for _ in range(3):
    t0 = utime.ticks_us(); t.shoe.shuffle(); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
print("RESULT shoe_shuffle_8_decks_us: mean=%d max=%d" % (sum(ts) // 3, max(ts)))

bands = []; real_band = lcd.show_band
def stamped(y, h): t0 = utime.ticks_us(); real_band(y, h); bands.append((t0, y, h, utime.ticks_diff(utime.ticks_us(), t0)))
lcd.show_band = stamped
shows = []; real_show = lcd.show
def tshow(): t0 = utime.ticks_us(); real_show(); shows.append((t0, utime.ticks_diff(utime.ticks_us(), t0)))
lcd.show = tshow
draws = []; real_draw_all = scr.draw_all
def tdraw(): t0 = utime.ticks_us(); real_draw_all(); draws.append(utime.ticks_diff(utime.ticks_us(), t0))
scr.draw_all = tdraw
save_t = []; real_save = ctx.store.save
def tsave(b): t0 = utime.ticks_us(); real_save(b); save_t.append(utime.ticks_diff(utime.ticks_us(), t0))
ctx.store.save = tsave

deal_t, slot_gap, card_band_push, card_band_draw, first_draw, result_draw, n_cards = [], [], [], [], [], [], []
move_t, shuffle_deals, mem = [], [], []
scr.draw_all()
real_hand = scr.hand_band
hb = []
def thand(side): t0 = utime.ticks_us(); real_hand(side); hb.append(utime.ticks_diff(utime.ticks_us(), t0))
scr.hand_band = thand
for c in range(250):
    if t.state == 'broke': scr.handle('A')
    k = ('RIGHT', 'LEFT', 'UP', 'DOWN')[c % 4]                  # a joystick move from the result
    bands.clear(); t0 = utime.ticks_us(); scr.handle(k); move_t.append(utime.ticks_diff(utime.ticks_us(), t0))
    bands.clear(); shows.clear(); draws.clear(); hb.clear()
    t0 = utime.ticks_us(); scr.handle('A'); dt = utime.ticks_diff(utime.ticks_us(), t0)
    if t.shuffled: shuffle_deals.append(dt); continue
    deal_t.append(dt); n_cards.append(len(t.coup.order))
    card = [b for b in bands if b[2] == 72]
    for b in card: card_band_push.append(b[3])
    for i in range(1, len(card)): slot_gap.append(utime.ticks_diff(card[i][0], card[i - 1][0]) // 1000)
    if draws: first_draw.append(draws[0]); result_draw.append(draws[-1])
    card_band_draw.extend(hb)
    if c % 10 == 9:
        gc.collect(); mem.append(gc.mem_free())
def rep(n, xs, u='us'):
    if xs: print("RESULT %s: n=%d mean=%d max=%d %s" % (n, len(xs), sum(xs) // len(xs), max(xs), u))
rep("deal_total (redraw, cards at 300 ms, result redraw, save)", deal_t)
rep("cards_per_coup", n_cards, '')
rep("deal_full_redraw_draw_all (incl show)", first_draw); rep("result_redraw_draw_all (incl show)", result_draw)
rep("card_band_draw (hand_band)", card_band_draw); rep("card_band_push (72 rows)", card_band_push)
rep("card_to_card_gap", slot_gap, 'ms (target 300)')
rep("joystick_move_from_result (top+bottom bands)", move_t)
rep("deal_with_shuffle (incl 700 ms Shuffling...)", shuffle_deals)
rep("save", save_t)
print("RESULT mem_free_every_10_coups=%s" % mem)
print("RESULT bankroll=%d history=%d seats=%s" % (t.bankroll.balance, len(t.history), t.seats.chips))
lcd.show_band = real_band; lcd.show = real_show
gc.collect(); m0 = gc.mem_free(); t0 = utime.ticks_us(); scr.paytable(); dt = utime.ticks_diff(utime.ticks_us(), t0)
gc.collect(); print("RESULT paytable_total_us=%d mem_before=%d mem_after=%d baccarat_pay_loaded=%s" % (dt, m0, gc.mem_free(), 'baccarat_pay' in sys.modules))
for f in ('/_bench_save.json', '/_bench_save.bak'):
    try: os.remove(f)
    except OSError: pass
gc.collect(); print("RESULT end mem_free=%d" % gc.mem_free())
