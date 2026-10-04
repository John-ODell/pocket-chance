# stud_rail_bench.py: DR-041 (Caribbean Stud AI seat rail). Five seats, each dealt five real cards from
# the same deck, each deciding with stud_rules.advice() against the dealer's up-card; a 12 px rail at
# y 228-239 with five chip stacks (up to six 2 px lines each) and a 4x4 green/red marker. Measures the
# engine time per seat and for five seats, the rail drawing, the bottom-band push, and seat RAM.
import sys, gc, utime
if '/games' not in sys.path: sys.path.append('/games')
from clocks import fast_peripherals; fast_peripherals()
from lcd import LCD
lcd = LCD(62_500_000); gc.collect()
import random
from pixfmt import rgb
import stud_rules, poker
from cards import card_name
GOLD = rgb(240, 200, 60); GREEN = rgb(40, 200, 60); RED = rgb(200, 20, 20); FELT = rgb(0, 90, 40)
random.seed(1618)
deck = list(range(52))
for i in range(51, 0, -1):
    j = random.randrange(i + 1); deck[i], deck[j] = deck[j], deck[i]
dealer = deck[0:5]; player = deck[5:10]
gc.collect(); m0 = gc.mem_free()
seats = [[list(deck[10 + 5*k: 15 + 5*k]), 1000, 0] for k in range(5)]   # cards, chips, last result
gc.collect(); print("RESULT five_seats_state_ram=%d bytes" % (m0 - gc.mem_free()))
print("RESULT stud_rules has: %s" % [n for n in dir(stud_rules) if not n.startswith('_')][:20])
adv = getattr(stud_rules, 'advice', None)
def decide(cards):
    """What a seat does per hand: evaluate its five cards, then the published strategy vs the up-card."""
    value = poker.evaluate(cards)
    return adv(cards, value, dealer[0]) if adv else None
ts = []
for k in range(5):
    t0 = utime.ticks_us(); r = decide(seats[k][0]); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
print("RESULT advice_per_seat_us=%s total_five_seats_us=%d sample=%r" % (ts, sum(ts), r))
t0 = utime.ticks_us()
for k in range(5): poker.evaluate(seats[k][0])
print("RESULT settle_five_seats_evaluate_us=%d (plus the dealer compare, 1 ms each)" % utime.ticks_diff(utime.ticks_us(), t0))
def rail():
    lcd.fill_rect(0, 228, 240, 12, FELT)
    for k in range(5):
        x = 16 + k * 44
        n = min(6, max(0, seats[k][1] // 200))
        for i in range(n): lcd.hline(x, 239 - i * 2, 20, GOLD)
        lcd.fill_rect(x + 24, 232, 4, 4, GREEN if seats[k][2] >= 0 else RED)
ts = []
for i in range(10):
    t0 = utime.ticks_us(); rail(); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
print("RESULT rail_draw_us mean=%d" % (sum(ts) // 10))
ts = []
for i in range(6):
    t0 = utime.ticks_us(); rail(); lcd.show_band(228, 12); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
print("RESULT rail_draw_plus_12row_push_us mean=%d max=%d" % (sum(ts) // 6, max(ts)))
ts = []
for i in range(6):
    t0 = utime.ticks_us(); lcd.fill_rect(0, 168, 240, 72, FELT); rail(); lcd.show_band(168, 72); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
print("RESULT bottom_band_72rows_with_rail_us mean=%d" % (sum(ts) // 6))
gc.collect(); print("RESULT end free=%d" % gc.mem_free())
lcd.fill(0); lcd.show()
