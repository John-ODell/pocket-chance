# baccarat_bench.py: DR-052 / DR-055 / DR-060 before the baccarat screen exists, with the real card
# primitives (games/blackjack.py Screen.card/card_back/felt), real lib/ (step 1n), real LCD at 62.5 MHz.
# Layout from DR-052: Stud's bands (top 0-23, banker 24-95 cards y 28, player 96-167 cards y 100,
# bottom 168-239) with cards at x 56/100/144; three bet boxes y 172-196 at x 8-78 / 85-155 / 162-232;
# prompt y 202; DR-060 history: twelve 8x8 squares y 214-222 at x 8 + 18k; DR-055 rail y 228-239 (five
# stacks). Measures: full redraw with six cards (drawn, then from a temp card sheet), the 72-row band
# push per dealt card, the clocked deal cadence (P, B, P, B, then two third cards at 300 ms), the
# bottom band with boxes + prompt + history + rail, history and rail draws alone, five seats' habit
# and settle, RAM. Temp sheet removed; no saves touched; soft reset after returns the board to main.py.
import sys, gc, utime, os
if '/games' not in sys.path: sys.path.append('/games')
import machine
machine.freq(125_000_000, 125_000_000)      # DR-050: lib/clocks.py is gone; the documented call does the same
from lcd import LCD
lcd = LCD(62_500_000); gc.collect()
import random, font
from art import Assets
from bankroll import Bankroll
from pixfmt import rgb
import blackjack
from blackjack import GOLD, WHITE, GREY, CARD_W, CARD_H, FELT
class Keys:
    def poll(self): return []
class Store:
    def save(self, b): pass
class Ctx: pass
ctx = Ctx(); ctx.lcd = lcd; ctx.assets = Assets('/assets'); ctx.buttons = Keys(); ctx.store = Store(); ctx.rng = random; ctx.bankroll = Bankroll(1000)
scr = blackjack.Screen(ctx)
random.seed(8086)
deck = list(range(52))
for i in range(51, 0, -1):
    j = random.randrange(i + 1); deck[i], deck[j] = deck[j], deck[i]
player, banker = deck[0:3], deck[3:6]
CX = (56, 100, 144); BY, PY = 28, 100
BLUE = rgb(40, 80, 220); RED = rgb(200, 20, 20); GREEN = rgb(40, 200, 60)
SEATS = [[1000, 0] for _ in range(5)]; history = []
def hand_band(y0, cards, label, y_cards):
    scr.felt(y0, 72)
    for i, c in enumerate(cards): scr.card(c, CX[i], y_cards)
    font.text(lcd, '%s  %d' % (label, sum(c % 13 for c in cards) % 10), 56, y_cards + CARD_H + 2, WHITE, 1)
def top_band(): scr.felt(0, 24); font.text(lcd, '$1000', 6, 4, GOLD, 2); font.text_right(lcd, 'stake 20', 234, 8, WHITE, 1)
def boxes(sel):
    for i, (x, name, pay) in enumerate(((8, 'PLAYER', '1:1'), (85, 'TIE', '8:1'), (162, 'BANKER', '19:20'))):
        lcd.fill_rect(x, 172, 70, 24, rgb(0, 60, 25)); lcd.rect(x, 172, 70, 24, GOLD if i == sel else GREY)
        font.text(lcd, name, x + 4, 175, WHITE, 1); font.text(lcd, pay, x + 4, 186, GREY, 1)
        if i == sel: font.text_right(lcd, '20', x + 66, 186, GOLD, 1)
def history_strip():
    for k, r in enumerate(history[-12:]):
        lcd.fill_rect(8 + 18 * k, 214, 8, 8, (BLUE, RED, GREEN)[r])
def rail():
    lcd.fill_rect(0, 228, 240, 12, FELT)
    for k in range(5):
        x = 10 + k * 44; n = min(6, max(0, SEATS[k][0] // 200))
        for i in range(n): lcd.fill_rect(x + 8, 239 - 2 * i, 20, 1, GOLD)
        if SEATS[k][1]: lcd.fill_rect(x + 1, 232, 4, 4, GREEN if SEATS[k][1] > 0 else RED)
def bottom_band(result):
    scr.felt(168, 72); boxes(2)
    font.text_centred(lcd, result or 'joystick: bet   A deal   X pays   B menu', 120, 202, GOLD if result else WHITE, 1)
    history_strip(); rail()
def full(np, nb, result):
    top_band(); hand_band(24, banker[:nb], 'BANKER', BY); hand_band(96, player[:np], 'PLAYER', PY); bottom_band(result); lcd.show()
def seats_coup(winner):
    # DR-055 habits: 1 banker, 2 player, 3 follows last winner, 4 against, 5 banker (tie every 5th)
    last = history[-1] if history else 1
    picks = (1, 0, last if last != 2 else 1, 0 if last == 1 else 1, 1 if len(history) % 5 else 2)
    for k in range(5):
        if picks[k] == winner: SEATS[k][0] += 20 if winner == 0 else (160 if winner == 2 else 19); SEATS[k][1] = 1
        elif winner == 2 and picks[k] != 2: SEATS[k][1] = 0           # tie: side bets push
        else: SEATS[k][0] -= 20; SEATS[k][1] = -1
def bench(label):
    ts = []
    for k in range(6):
        t0 = utime.ticks_us(); full(3, 3, 'BANKER WINS 8-6   -20' if k & 1 else None); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
    print("RESULT full_redraw_6_cards %s: mean_us=%d max_us=%d" % (label, sum(ts) // 6, max(ts)))
    # band push per dealt card: 72-row band with 1, 2, 3 cards + total line
    for n in (1, 2, 3):
        t0 = utime.ticks_us(); hand_band(96, player[:n], 'PLAYER', PY); lcd.show_band(96, 72); dt = utime.ticks_diff(utime.ticks_us(), t0)
        print("RESULT deal_step_band_%dcards %s: us=%d" % (n, label, dt))
    # clocked deal: P, B, P, B then third cards, by the clock
    stamps = []; seq = ((96, player, 1, PY, 'PLAYER'), (24, banker, 1, BY, 'BANKER'), (96, player, 2, PY, 'PLAYER'), (24, banker, 2, BY, 'BANKER'), (96, player, 3, PY, 'PLAYER'), (24, banker, 3, BY, 'BANKER'))
    full(0, 0, None); t_prev = utime.ticks_us()
    for y0, cards, n, yc, lab in seq:
        t0 = utime.ticks_us(); hand_band(y0, cards[:n], lab, yc); lcd.show_band(y0, 72); spent = utime.ticks_diff(utime.ticks_us(), t0)
        stamps.append(utime.ticks_diff(utime.ticks_us(), t_prev) // 1000); t_prev = utime.ticks_us()
        utime.sleep_ms(max(0, 300 - spent // 1000))
    print("RESULT deal_cadence_ms %s: %s (each = push time; target spacing 300 ms incl. sleep)" % (label, stamps[1:]))
    ts = []
    for k in range(6):
        t0 = utime.ticks_us(); bottom_band('TIE   +160' if k & 1 else None); lcd.show_band(168, 72); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
    print("RESULT bottom_band_boxes_prompt_history_rail_push %s: mean_us=%d max_us=%d" % (label, sum(ts) // 6, max(ts)))
history.extend([1, 0, 0, 1, 2, 1, 1, 0, 1, 0, 0, 1])
for k in range(5): SEATS[k] = [1000 - 40 * k, (k % 3) - 1]
t0 = utime.ticks_us(); history_strip(); t_h = utime.ticks_diff(utime.ticks_us(), t0)
t0 = utime.ticks_us(); rail(); t_r = utime.ticks_diff(utime.ticks_us(), t0)
t0 = utime.ticks_us()
for c in range(20): seats_coup((c * 7) % 3)
t_s = utime.ticks_diff(utime.ticks_us(), t0) // 20
print("RESULT history_12_squares_draw_us=%d rail_draw_us=%d seats_habit_and_settle_per_coup_us=%d seats_state_bytes~%d" % (t_h, t_r, t_s, 5 * 2 * 8 + 12))
gc.collect(); print("RESULT ram_free_after_primitives=%d (no baccarat module; dev estimates ~15 KB for it)" % gc.mem_free())
bench("code_drawn")
W, H, N = 40, 56, 53
try:
    with open('/assets/cards.565', 'wb') as f:
        f.write(bytes([W & 255, W >> 8, (H * N) & 255, (H * N) >> 8])); r = bytes([0x12, 0x34]) * W
        for k in range(N):
            for y in range(H): f.write(r)
    ctx.assets.missing.clear(); ctx.assets.known.clear()
    if hasattr(ctx.assets, 'use_sheets'): ctx.assets.use_sheets(('cards',))
    print("RESULT sheet_open=%s" % (list(getattr(ctx.assets, 'open_sheets', {}).keys()),))
    bench("sheet_cards")
    if hasattr(ctx.assets, 'release_sheets'): ctx.assets.release_sheets()
finally:
    try: os.remove('/assets/cards.565')
    except OSError: pass
    print("RESULT cleanup assets=%s" % os.listdir('/assets'))
gc.collect(); print("RESULT end mem_free=%d" % gc.mem_free())
