# bounce.py: button/joystick bounce and press length. Samples every input at ~20 kHz for 8 s
# while a human presses keys, and logs every edge with a microsecond stamp. Reports, per pin,
# how many edges came within 5 ms of a previous edge (bounce) and press durations.
from machine import Pin
import utime
names = {15:'A',17:'B',19:'X',21:'Y',2:'up',18:'down',16:'left',20:'right',3:'press'}
pins = [(g, Pin(g, Pin.IN, Pin.PULL_UP)) for g in names]
last = {g: 1 for g in names}
edges = []  # (us, gpio, value)
print("PRESS KEYS NOW for 8 seconds")
t_end = utime.ticks_add(utime.ticks_us(), 8_000_000)
n = 0
while utime.ticks_diff(t_end, utime.ticks_us()) > 0:
    now = utime.ticks_us()
    for g, p in pins:
        v = p.value()
        if v != last[g]:
            edges.append((now, g, v)); last[g] = v
    n += 1
print("RESULT samples=%d rate_Hz=%d edges=%d" % (n, n // 8, len(edges)))
by = {}
for t, g, v in edges: by.setdefault(g, []).append((t, v))
for g, ev in by.items():
    bounce = sum(1 for i in range(1, len(ev)) if utime.ticks_diff(ev[i][0], ev[i-1][0]) < 5000)
    presses = [utime.ticks_diff(ev[i+1][0], ev[i][0]) for i in range(len(ev)-1) if ev[i][1] == 0]
    gaps = [utime.ticks_diff(ev[i][0], ev[i-1][0]) for i in range(1, len(ev))]
    print("RESULT %s(GP%d) edges=%d edges_within_5ms=%d min_gap_us=%d press_ms=%s" %
          (names[g], g, len(ev), bounce, min(gaps) if gaps else -1, [p // 1000 for p in presses][:8]))
