# pin_hunt.py: READ-ONLY hunt for which GPIO a key really sits on. Every GPIO except the LCD pins
# (8-13) and the power-sense pins (23, 24, 25, 29) is set as an input with a weak pull-up, then
# sampled for DUR_S seconds. Any pin that goes low while a human presses one key is a candidate.
# Nothing is driven as an output.
from machine import Pin
import utime
DUR_S = 30
SKIP = {8, 9, 10, 11, 12, 13, 23, 24, 25, 29}
gp = [g for g in range(30) if g not in SKIP]
pins = [(g, Pin(g, Pin.IN, Pin.PULL_UP)) for g in gp]
utime.sleep_ms(20)
idle = {g: p.value() for g, p in pins}
print("RESULT idle_low_pins=%s (low at rest = not a key, ignore)" % [g for g in gp if idle[g] == 0])
last = dict(idle); edges = []
print("PRESS NOW for %d s" % DUR_S)
t_end = utime.ticks_add(utime.ticks_us(), DUR_S * 1_000_000)
while utime.ticks_diff(t_end, utime.ticks_us()) > 0:
    now = utime.ticks_us()
    for g, p in pins:
        v = p.value()
        if v != last[g]:
            edges.append((now, g, v)); last[g] = v
first = {}
for t, g, v in edges:
    if v == 0 and idle[g] == 1 and g not in first: first[g] = t
order = [g for g, t in sorted(first.items(), key=lambda kv: kv[1])]
print("RESULT pins_that_went_low_in_order=%s" % order)
for g in order:
    ev = [(t, v) for t, gg, v in edges if gg == g]
    presses = [utime.ticks_diff(ev[i+1][0], ev[i][0]) // 1000 for i in range(len(ev)-1) if ev[i][1] == 0]
    print("RESULT GP%d presses=%d press_ms=%s" % (g, len(presses), presses[:8]))
