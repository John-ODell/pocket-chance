# holdem_bench.py: DR-034 / DR-035 / DR-038 (Ultimate Texas Hold'em) measured before the screen
# exists, with the real blackjack card primitives, real lib/, lib/poker.py from the board (step 1j).
# Layout (DR-034): top 0-23; dealer row y 24-83 with cards at x 76/120 and seat strips at x 8 and 172;
# community row y 84-143, cards at x 12/56/100/144/188; player row y 144-203 with cards x 76/120 and
# strips at x 8/172; bottom 204-239 size-1 text. Times full redraws (code-drawn, then a temp card
# sheet), band pushes, strip draws, and the AI decision cost (poker.evaluate on 5/6/7 cards, per seat,
# four seats + dealer + player per phase) against the 300 ms cadence; RAM of four seats' state.
import sys, gc, utime, os
if '/games' not in sys.path: sys.path.append('/games')
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
scr = blackjack.Screen(ctx)
random.seed(2718)
deck = list(range(52))
for i in range(51, 0, -1):
    j = random.randrange(i + 1); deck[i], deck[j] = deck[j], deck[i]
dealer, player, community = deck[0:2], deck[2:4], deck[4:9]
seats_cards = [deck[9 + 2*k: 11 + 2*k] for k in range(4)]
NAMES = ('Ann', 'Bo', 'Cy', 'Dee')
gc.collect(); m0 = gc.mem_free()
seats = [{'name': NAMES[k], 'chips': 1000, 'status': 'check', 'cards': list(seats_cards[k])} for k in range(4)]
gc.collect(); print("RESULT four_seats_state_ram=%d bytes" % (m0 - gc.mem_free()))
DX = (76, 120); CX = (12, 56, 100, 144, 188); DY, CY, PY = 28, 88, 148
STRIP_X = (8, 172)
def strip(k, y, status):
    x = STRIP_X[k % 2]
    lcd.rect(x, y, 60, 56, GREY)
    font.text(lcd, seats[k]['name'], x + 4, y + 6, WHITE, 1)
    font.text(lcd, '$%d' % seats[k]['chips'], x + 4, y + 22, GOLD, 1)
    font.text(lcd, status, x + 4, y + 38, GREY, 1)
def top_band():
    scr.felt(0, 24); font.text(lcd, '$1000', 6, 4, GOLD, 2); font.text_right(lcd, 'ante 10 blind 10 play 40', 234, 8, WHITE, 1)
def dealer_band(up):
    scr.felt(24, 60)
    for i, c in enumerate(dealer):
        if i < up: scr.card(c, DX[i], DY)
        else: scr.card_back(DX[i], DY)
    strip(0, 24, 'raise 4x'); strip(1, 24, 'fold')
def community_band(up):
    scr.felt(84, 60)
    for i, c in enumerate(community):
        if i < up: scr.card(c, CX[i], CY)
        else: scr.card_back(CX[i], CY)
def player_band():
    scr.felt(144, 60)
    for i, c in enumerate(player): scr.card(c, DX[i], PY)
    strip(2, 144, 'check'); strip(3, 144, 'WIN +40')
def bottom_band(result):
    scr.felt(204, 36)
    font.text_centred(lcd, ('YOU WIN +40: two pair' if result else 'Flop: A check  B play 2x'), 120, 206, GOLD if result else WHITE, 1)
    font.text_centred(lcd, 'X bet 4x   B fold', 120, 218, WHITE, 1)
    font.text_centred(lcd, 'joystick: ante', 120, 228, GREY, 1)
def full(up_d, up_c, result):
    top_band(); dealer_band(up_d); community_band(up_c); player_band(); bottom_band(result); lcd.show()
def bench(label):
    ts = []
    for k in range(6):
        t0 = utime.ticks_us(); full(2, 5, bool(k & 1)); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
    print("RESULT full_redraw_9_cards_4_strips %s: mean_us=%d max_us=%d" % (label, sum(ts) // 6, max(ts)))
    ts = []
    for k in range(6):
        t0 = utime.ticks_us(); full(0, 0, False); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
    print("RESULT full_redraw_deal_7_backs %s: mean_us=%d max_us=%d" % (label, sum(ts) // 6, max(ts)))
    ts = []
    for up in (3, 5, 3, 5):
        t0 = utime.ticks_us(); community_band(up); lcd.show_band(84, 60); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
    print("RESULT community_band_push %s: mean_us=%d max_us=%d (flop 3 up / river 5 up, 60 rows)" % (label, sum(ts) // 4, max(ts)))
    ts = []
    for up in (1, 2, 1, 2):
        t0 = utime.ticks_us(); dealer_band(up); lcd.show_band(24, 60); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
    print("RESULT dealer_band_push %s: mean_us=%d max_us=%d (2 cards + 2 strips, 60 rows)" % (label, sum(ts) // 4, max(ts)))
    ts = []
    for k in range(4):
        t0 = utime.ticks_us(); scr.felt(144, 60); player_band(); lcd.show_band(144, 60); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
    print("RESULT one_strip_update_via_row_band %s: mean_us=%d (player row redrawn + 60-row push)" % (label, sum(ts) // 4))
    t0 = utime.ticks_us()
    for k in range(4): strip(k, 24 if k < 2 else 144, 'check')
    print("RESULT four_strips_draw_only %s: us=%d" % (label, utime.ticks_diff(utime.ticks_us(), t0)))
    # DR-044 rev 2: a 24x24 chip-stack sprite per seat box instead of the text strip
    ts = []
    for k in range(8):
        t0 = utime.ticks_us(); ok = ctx.assets.blit(lcd, 'chip_25', STRIP_X[k % 2] + 18, (24 if k % 4 < 2 else 144) + 16)
        if not ok: scr.chip(25, STRIP_X[k % 2] + 18, (24 if k % 4 < 2 else 144) + 16)
        ts.append(utime.ticks_diff(utime.ticks_us(), t0))
    print("RESULT chip_stack_24x24_per_seat %s: mean_us=%d (sheet blit if a chips sheet is open, else code-drawn chip) ok=%s" % (label, sum(ts) // 8, ok))
# AI cost, the way DR-035 will spend it
def ev(cards, n):
    t0 = utime.ticks_us()
    for _ in range(n): poker.evaluate(cards)
    return utime.ticks_diff(utime.ticks_us(), t0) // n
e5 = ev(seats[0]['cards'] + community[:3], 10); e6 = ev(seats[0]['cards'] + community[:4], 5); e7 = ev(seats[0]['cards'] + community, 3)
print("RESULT poker.evaluate us: flop(5 cards, 1 combo)=%d turn(6 cards, 6 combos)=%d river(7 cards, 21 combos)=%d" % (e5, e6, e7))
t0 = utime.ticks_us()
for k in range(4): poker.evaluate(seats[k]['cards'] + community)
poker.evaluate(dealer + community); poker.evaluate(player + community)
showdown = utime.ticks_diff(utime.ticks_us(), t0)
print("RESULT showdown_phase_6_hands_7_cards_us=%d (4 seats + dealer + player; must fit before the first dealer flip or in a 300 ms gap)" % showdown)
t0 = utime.ticks_us()
for k in range(4): poker.evaluate(seats[k]['cards'] + community[:3])
print("RESULT flop_phase_4_seats_5_cards_us=%d" % utime.ticks_diff(utime.ticks_us(), t0))
t0 = utime.ticks_us(); gc.collect(); print("RESULT gc_pause_us=%d" % utime.ticks_diff(utime.ticks_us(), t0))
bench("code_drawn")
gc.collect(); print("RESULT ram_after_code_drawn free=%d" % gc.mem_free())
W, H, N = 40, 56, 53
try:
    with open('/assets/cards.565', 'wb') as f:
        f.write(bytes([W & 255, W >> 8, (H * N) & 255, (H * N) >> 8])); r = bytes([0x12, 0x34]) * W
        for k in range(N):
            for y in range(H): f.write(r)
    with open('/assets/chips.565', 'wb') as f:                     # 5 x 24x24 chips (sheets.py order)
        f.write(bytes([24, 0, 120, 0])); r = bytes([0x12, 0x34]) * 24
        for k in range(5 * 24): f.write(r)
    ctx.assets.missing.clear(); ctx.assets.known.clear()
    if hasattr(ctx.assets, 'use_sheets'): ctx.assets.use_sheets(('cards', 'chips'))
    print("RESULT sheet_open=%s" % (list(getattr(ctx.assets, 'open_sheets', {}).keys()),))
    bench("sheet_cards")
    if hasattr(ctx.assets, 'release_sheets'): ctx.assets.release_sheets()
finally:
    for p in ('/assets/cards.565', '/assets/chips.565'):
        try: os.remove(p)
        except OSError: pass
    print("RESULT cleanup assets=%s" % os.listdir('/assets'))
gc.collect(); print("RESULT end free=%d" % gc.mem_free())
full(2, 5, True); print("RESULT leaving the 9-card result layout on screen (code-drawn)")
