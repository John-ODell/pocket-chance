# frame_full.py: full-frame push. Python-side fill vs wire time, over 100 frames, at the clock
# given below (change BAUD to the value spi_clock.py shows is usable). Look at the panel: it should
# cycle 4 solid colours; flicker/garbage at a given clock means the panel rejects it.
from lcdbench import Bench, stats
import utime
BAUD = 62_500_000
N = 100
b = Bench(baud=BAUD)
print("RESULT frame_baud_requested=%d granted=%s" % (BAUD, b.granted))
cols = (0xF800, 0x07E0, 0x001F, 0xFFFF)
fill_t, wire_t, tot_t = [], [], []
for i in range(N):
    t0 = utime.ticks_us()
    b.fb.fill(cols[i & 3])
    t1 = utime.ticks_us()
    b.show()
    t2 = utime.ticks_us()
    fill_t.append(utime.ticks_diff(t1, t0)); wire_t.append(utime.ticks_diff(t2, t1))
    tot_t.append(utime.ticks_diff(t2, t0))
stats("full_fill", fill_t); stats("full_wire", wire_t); stats("full_total", tot_t)
# Heavier Python drawing: 20 filled rects + 10 text lines per frame, then push
t = []
for i in range(50):
    t0 = utime.ticks_us()
    b.fb.fill(0)
    for k in range(20):
        b.fb.fill_rect((k * 11) % 200, (k * 7) % 200, 30, 30, 0xF800 + k * 37)
    for k in range(10):
        b.fb.text("Pocket Chance", 0, k * 12, 0xFFFF)
    b.show()
    t.append(utime.ticks_diff(utime.ticks_us(), t0))
stats("full_busyscene", t)
b.blank()
