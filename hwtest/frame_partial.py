# frame_partial.py: partial redraw strategies. Moves a 48x48 box across a 240x240 scene and
# pushes only what changed. Strategies: (a) rect window from a small sprite buffer,
# (b) full-width band of rows (contiguous in the framebuffer), (c) dirty rect covering old+new box
# copied row by row into a scratch buffer. Reports fps for each.
from lcdbench import Bench, stats
import utime, framebuf
BAUD = 62_500_000
N = 150
b = Bench(baud=BAUD)
print("RESULT partial_baud_requested=%d granted=%s" % (BAUD, b.granted))
b.fb.fill(0x0000)
for y in range(0, 240, 20):
    b.fb.fill_rect(0, y, 240, 10, 0x2104)
b.show()
S = 48
spr = bytearray(S * S * 2)
sfb = framebuf.FrameBuffer(spr, S, S, framebuf.RGB565)
sfb.fill(0xF800); sfb.rect(0, 0, S, S, 0xFFFF)

# (a) sprite moves; the bar background is redrawn into a scratch the size of old+new bounding box
t = []
x = 0
for i in range(N):
    nx = (x + 3) % (240 - S)
    bw = abs(nx - x) + S           # bounding width of old+new
    bx = min(x, nx)
    scratch = bytearray(bw * S * 2)
    sc = framebuf.FrameBuffer(scratch, bw, S, framebuf.RGB565)
    t0 = utime.ticks_us()
    sc.fill(0)
    for yy in range(0, S, 20):
        sc.fill_rect(0, yy, bw, 10, 0x2104)
    sc.blit(sfb, nx - bx, 0)
    b.window(bx, 100, bw, S)
    b.push(scratch)
    t.append(utime.ticks_diff(utime.ticks_us(), t0))
    x = nx
stats("partial_rect_scratch", t)

# (b) full-width band of 48 rows pushed straight from the main framebuffer (no copy)
t = []
x = 0
mv = memoryview(b.buf)
for i in range(N):
    x = (x + 3) % (240 - S)
    t0 = utime.ticks_us()
    b.fb.fill_rect(0, 100, 240, S, 0)
    b.fb.blit(sfb, x, 100)
    b.window(0, 100, 240, S)
    b.push(mv[100 * 480:(100 + S) * 480])
    t.append(utime.ticks_diff(utime.ticks_us(), t0))
stats("partial_band", t)

# (c) tiny update: 8x8 digit-sized region (typical score change)
t = []
for i in range(N):
    t0 = utime.ticks_us()
    b.fb.fill_rect(10, 10, 8, 8, i * 97 & 0xFFFF)
    b.window(10, 10, 8, 8)
    # 8 rows of 16 bytes each are not contiguous in the main fb
    row = bytearray(128)
    for r in range(8):
        o = ((10 + r) * 240 + 10) * 2
        row[r * 16:(r + 1) * 16] = mv[o:o + 16]
    b.push(row)
    t.append(utime.ticks_diff(utime.ticks_us(), t0))
stats("partial_8x8", t)
b.blank()
