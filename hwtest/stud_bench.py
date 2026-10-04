# stud_bench.py: DR-026 / DR-029 (Caribbean Stud) measured before the screen exists, with the real
# blackjack card primitives (games/blackjack.py Screen.card / card_back / felt), real lib/, real LCD.
# Layout from DR-026: cards 40x56 at x = 12,56,100,144,188; dealer row y 28, player row y 100; bands
# 0-23 / 24-95 / 96-167 / 168-239. Measures: 10-card full redraw + show (code-drawn, then from a
# temporary cards.565 sheet), the 72-row dealer band push with 5 cards (reveal step) x4 at 300 ms,
# a gc.collect() inside a reveal gap, raise/fold = dealer + bottom band pushes, poker.evaluate(),
# RAM for two 5-card hands. Temp sheet removed at the end. John's save untouched (no Store used).
import sys, gc, utime, os
if '/games' not in sys.path: sys.path.append('/games')
sys.path.insert(0, '/remote/stage')     # lib/poker.py is not on the board yet: staged from the mount
from clocks import fast_peripherals; fast_peripherals()
from lcd import LCD
lcd = LCD(62_500_000); gc.collect()
import random, font
from art import Assets
from bankroll import Bankroll
from cards import card_name
import poker, blackjack
from blackjack import GOLD, WHITE, GREY, CARD_W, CARD_H
class Keys:
    def poll(self): return []
class Store:
    def save(self, b): pass
class Ctx: pass
ctx = Ctx(); ctx.lcd = lcd; ctx.assets = Assets('/assets'); ctx.buttons = Keys(); ctx.store = Store(); ctx.rng = random; ctx.bankroll = Bankroll(1000)
scr = blackjack.Screen(ctx)           # for card(), card_back(), felt()
random.seed(99)
deck = list(range(52))
for i in range(51, 0, -1):            # MicroPython's random has no shuffle
    j = random.randrange(i + 1); deck[i], deck[j] = deck[j], deck[i]
dealer, player = deck[:5], deck[5:10]
gc.collect(); print("RESULT ram_ready free=%d" % gc.mem_free())
h2 = [list(dealer), list(player)]; gc.collect(); print("RESULT two_5card_hands_ram=%d bytes" % (0 if False else 2 * 5 * 8))
XS = (12, 56, 100, 144, 188); DY, PY = 28, 100
def row(cards, y, face_down_from=5):
    for i, c in enumerate(cards):
        if i >= face_down_from: scr.card_back(XS[i], y)
        else: scr.card(c, XS[i], y)
def dealer_band(up):
    scr.felt(24, 72); row(dealer, DY, up)
    font.text(lcd, 'Dealer shows %s' % card_name(dealer[0])[0] if up < 5 else 'Dealer: ' + poker.name(poker.evaluate(dealer)), 6, 86, WHITE, 1)
def player_band():
    scr.felt(96, 72); row(player, PY); font.text(lcd, 'You: ' + poker.name(poker.evaluate(player)), 6, 158, WHITE, 1)
def top_band(): scr.felt(0, 24); font.text(lcd, '$1000', 6, 4, GOLD, 2); font.text_right(lcd, 'ante 10', 234, 4, WHITE, 2)
def bottom_band(result):
    scr.felt(168, 72)
    if result:
        font.text_centred(lcd, 'YOU WIN', 120, 176, GOLD, 2); font.text_centred(lcd, '+30: ante 10, raise 20 x 1', 120, 204, WHITE, 1); font.text_centred(lcd, 'A next   B menu', 120, 218, WHITE, 1)
    else:
        font.text_centred(lcd, 'A raise 20   B fold', 120, 218, WHITE, 1)
def full_redraw(up, result):
    top_band(); dealer_band(up); player_band(); bottom_band(result); lcd.show()
def bench_full(label):
    ts = []
    for k in range(6):
        t0 = utime.ticks_us(); full_redraw(1 if k & 1 else 5, bool(k & 1)); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
    print("RESULT full_redraw_10_cards %s: mean_us=%d max_us=%d" % (label, sum(ts) // 6, max(ts)))
def bench_reveal(label):
    ts = []; gcs = []
    for up in (2, 3, 4, 5):
        t0 = utime.ticks_us(); dealer_band(up); lcd.show_band(24, 72); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
        t1 = utime.ticks_us(); gc.collect(); gcs.append(utime.ticks_diff(utime.ticks_us(), t1))   # the pause a gc would add inside the 300 ms gap
        utime.sleep_ms(300 - (ts[-1] + gcs[-1]) // 1000)
    print("RESULT reveal_step_72row_band %s: mean_us=%d max_us=%d; gc_pause_in_gap_us mean=%d max=%d" % (label, sum(ts) // 4, max(ts), sum(gcs) // 4, max(gcs)))
def bench_raise(label):
    ts = []
    for k in range(4):
        t0 = utime.ticks_us(); dealer_band(1); lcd.show_band(24, 72); bottom_band(False); lcd.show_band(168, 72); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
    print("RESULT raise_or_fold_two_bands %s: mean_us=%d max_us=%d" % (label, sum(ts) // 4, max(ts)))
t0 = utime.ticks_us()
for _ in range(20): poker.evaluate(player)
e5 = utime.ticks_diff(utime.ticks_us(), t0) // 20
t0 = utime.ticks_us()
for _ in range(5): poker.evaluate(deck[:7])
e7 = utime.ticks_diff(utime.ticks_us(), t0) // 5
print("RESULT poker.evaluate us: 5_cards=%d 7_cards=%d" % (e5, e7))
bench_full("code_drawn"); bench_reveal("code_drawn"); bench_raise("code_drawn")
gc.collect(); print("RESULT ram_after_code_drawn free=%d" % gc.mem_free())
# temporary full card sheet so every card takes the art path; reuse the existing Assets (a second
# instance would need another 16 KB scratch). Clear its miss/known caches so the sheet is probed.
W, H, N = 40, 56, 53
try:
    with open('/assets/cards.565', 'wb') as f:
        f.write(bytes([W & 255, W >> 8, (H * N) & 255, (H * N) >> 8])); r = bytes([0x12, 0x34]) * W
        for k in range(N):
            for y in range(H): f.write(r)
    ctx.assets.missing.clear(); ctx.assets.known.clear()
    if hasattr(ctx.assets, 'use_sheets'): ctx.assets.use_sheets(('cards',))
    print("RESULT sheet_open=%s" % (list(getattr(ctx.assets, 'open_sheets', {}).keys()),))
    bench_full("sheet_cards"); bench_reveal("sheet_cards"); bench_raise("sheet_cards")
    if hasattr(ctx.assets, 'release_sheets'): ctx.assets.release_sheets()
    gc.collect(); print("RESULT ram_after_sheet free=%d" % gc.mem_free())
finally:
    try: os.remove('/assets/cards.565')
    except OSError: pass
    print("RESULT cleanup assets=%s" % os.listdir('/assets'))
ctx.assets.missing.clear(); ctx.assets.known.clear()
full_redraw(5, True); print("RESULT leaving the 10-card result layout on screen (code-drawn)")
