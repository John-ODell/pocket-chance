# split_bench.py: DR-016 cost check. Draws the split layout the dev proposes (two player hands side
# by side in the player band, up to 4 cards each at a 20 px step, 16 px gap, gold marker and total
# under the active hand, the other dimmed) using the real on-board lib/ and games/ code-drawn cards,
# and times the same 142-row band push a hit uses today. Also the RAM of a second hand.
# Run: mpremote connect <port> mount hwtest exec "import split_bench"   (needs UPLOAD.md step 1)
import sys, gc, utime
if '/games' not in sys.path:
    sys.path.append('/games')
from clocks import fast_peripherals
fast_peripherals()
from lcd import LCD
lcd = LCD(62_500_000)
gc.collect()
import random, font
from pixfmt import rgb
from art import Assets
from cards import hand_value
import blackjack
from blackjack import Screen, PLAYER_Y, BANNER_Y, CARD_W, CARD_H, GOLD, WHITE, GREY, FELT

class Ctx: pass
class Keys:
    def poll(self): return []
class Store:
    def save(self, b): pass
ctx = Ctx(); ctx.lcd = lcd; ctx.assets = Assets('/assets'); ctx.buttons = Keys(); ctx.store = Store()
ctx.rng = random;
from bankroll import Bankroll
ctx.bankroll = Bankroll()
scr = Screen(ctx)
scr.draw_all()

# a deck of card codes as cards.card_name expects them: reuse what the shoe deals
t = scr.table
t.deal()
r = t.round
while len(r.player) < 4 and t.state == 'playing':
    t.hit()
pool = list(r.player) + list(r.dealer)
while len(pool) < 8:
    pool += pool
hand_a = pool[:4]; hand_b = pool[4:8]

STEP = 20; HAND_W = CARD_W + 3 * STEP; GAP = 16
X0 = (240 - (2 * HAND_W + GAP)) // 2

def split_hand(cards, x, y, active):
    for i, c in enumerate(cards):
        scr.card(c, x + i * STEP, y)
    tot = hand_value(cards)[0]
    col = GOLD if active else GREY
    font.text(lcd, '%d' % tot, x, y + CARD_H + 2, col, 1)
    if active:
        lcd.fill_rect(x, y + CARD_H + 12, HAND_W, 2, GOLD)

def draw_split_band(n_a, n_b, active=0):
    scr.felt(PLAYER_Y - 6, BANNER_Y - PLAYER_Y + 6)
    split_hand(hand_a[:n_a], X0, PLAYER_Y, active == 0)
    split_hand(hand_b[:n_b], X0 + HAND_W + GAP, PLAYER_Y, active == 1)
    scr.draw_bottom()
    lcd.show_band(PLAYER_Y - 6, 240 - PLAYER_Y + 6)

gc.collect(); m0 = gc.mem_free()
second_hand = list(hand_b); second_bet = [35]
gc.collect(); print("RESULT second_hand_ram=%d bytes (4 cards + bet)" % (m0 - gc.mem_free()))

for n_a, n_b, label in ((2, 2, "2+2 cards, right after the split"), (3, 2, "3+2"), (4, 4, "4+4 worst case")):
    ts = []
    for _ in range(10):
        t0 = utime.ticks_us(); draw_split_band(n_a, n_b, _ & 1); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
    print("RESULT split_band %s: mean_us=%d max_us=%d (felt + %d code-drawn cards + totals + prompt + 142-row band)" % (label, sum(ts) // 10, max(ts), n_a + n_b))

# the same band with ONE hand of 3 cards, as today's hit path, for a like-for-like baseline
ts = []
for _ in range(10):
    t0 = utime.ticks_us(); scr.draw_player(); scr.draw_bottom(); lcd.show_band(PLAYER_Y - 6, 240 - PLAYER_Y + 6)
    ts.append(utime.ticks_diff(utime.ticks_us(), t0))
print("RESULT single_hand_band_today: mean_us=%d max_us=%d (%d cards)" % (sum(ts) // 10, max(ts), len(r.player)))
# per-card cost of a code-drawn card, to convert to the art case (~1 ms per blit)
ts = []
for _ in range(10):
    t0 = utime.ticks_us(); scr.card(hand_a[0], 10, 10); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
print("RESULT one_code_drawn_card_us=%d" % (sum(ts) // 10))
gc.collect(); print("RESULT end mem_free=%d" % gc.mem_free())
print("RESULT leaving the split layout on screen (4+4) for a look; widths: hand=%d gap=%d x0=%d right_edge=%d" % (HAND_W, GAP, X0, X0 + 2 * HAND_W + GAP))
draw_split_band(4, 4, 0)
