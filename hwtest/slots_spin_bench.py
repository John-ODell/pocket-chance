# slots_spin_bench.py: DR-020 option A measured with the real lib code before the slots screen exists.
# Per frame, per spinning reel: Assets.blit reads the two straddling 56x56 symbols from flash into a
# 56x56 compose FrameBuffer at the scroll offset (blit clips), the compose is copied into the main
# framebuffer at the window, and LCD.show_rect pushes that window. Also: pushing the compose buffer
# straight to the panel (no copy), one-reel frames (end of spin), DR-021's 3-window blink, and the
# same 3-reel frame with the peripheral clock back on the 48 MHz USB PLL (SPI 24 MHz, as shipped).
# Two stand-in symbol files are written to /assets as _bench_sym0/1.565 and removed at the end.
import sys, gc, utime, os, framebuf, machine
from clocks import fast_peripherals, is_fast
fast_peripherals()
from lcd import LCD
lcd = LCD(62_500_000); gc.collect()
from art import Assets
from pixfmt import rgb, KEY_BE
S = 56; N = S * S * 2
def write_sym(path, c1, c2):
    with open(path, 'wb') as f:
        f.write(bytes([S & 255, S >> 8, S & 255, S >> 8]))
        row_a = bytes([c1 >> 8, c1 & 255]) * S
        row_b = bytes([c2 >> 8, c2 & 255]) * S
        key = bytes([KEY_BE >> 8, KEY_BE & 255])
        for y in range(S):
            r = bytearray(row_a if (y // 8) & 1 else row_b)
            if y < 6 or y >= S - 6:            # transparent margin, so the key path is exercised
                r = bytearray(key * S)
            f.write(r)
write_sym('/assets/_bench_sym0.565', 0xF800, 0xFFE0)   # red / yellow stripes
write_sym('/assets/_bench_sym1.565', 0x07E0, 0x001F)   # green / blue stripes
assets = Assets('/assets')
gc.collect(); m_before = gc.mem_free()
compose_buf = bytearray(N)                               # the dev slices this from the 16 KB scratch
compose = framebuf.FrameBuffer(compose_buf, S, S, framebuf.RGB565)
gc.collect(); print("RESULT ram: free_before_compose=%d after=%d (compose %d B; Assets scratch %d B already counted)" % (m_before, gc.mem_free(), N, len(assets.scratch)))
WIN_X = (18, 92, 166); WIN_Y = 100
lcd.fill(rgb(40, 20, 10))
for x in WIN_X: lcd.rect(x - 2, WIN_Y - 2, S + 4, S + 4, rgb(240, 200, 60))
lcd.show()
names = ('_bench_sym0', '_bench_sym1')

def reel_frame(x, off, copy_then_rect=True):
    """One reel at scroll offset off (0..55): two symbol blits into compose, then to the panel."""
    compose.fill(0)
    assets.blit(compose, names[0], 0, -off)
    assets.blit(compose, names[1], 0, S - off)
    if copy_then_rect:
        lcd.blit(compose, x, WIN_Y)
        lcd.show_rect(x, WIN_Y, S, S, compose_buf)     # the dev's description (copy rows, push)
    else:
        lcd._window(x, WIN_Y, S, S); lcd._push(compose_buf)   # push compose directly, no copy

def run(label, reels, frames=100, copy=True):
    ts = []; off = 0
    for i in range(frames):
        t0 = utime.ticks_us()
        for x in reels: reel_frame(x, off, copy)
        ts.append(utime.ticks_diff(utime.ticks_us(), t0)); off = (off + 8) % S
    print("RESULT %s: mean_us=%d max_us=%d fps=%.1f (%d frames, 8 px/frame)" % (label, sum(ts) // len(ts), max(ts), 1e6 * len(ts) / sum(ts), len(ts)))

# sub-timings at 62.5 MHz
t0 = utime.ticks_us(); compose.fill(0); assets.blit(compose, names[0], 0, -24); assets.blit(compose, names[1], 0, S - 24); t_comp = utime.ticks_diff(utime.ticks_us(), t0)
t0 = utime.ticks_us(); lcd.blit(compose, WIN_X[0], WIN_Y); t_copy = utime.ticks_diff(utime.ticks_us(), t0)
t0 = utime.ticks_us(); lcd.show_rect(WIN_X[0], WIN_Y, S, S, compose_buf); t_rect = utime.ticks_diff(utime.ticks_us(), t0)
t0 = utime.ticks_us(); lcd._window(WIN_X[0], WIN_Y, S, S); lcd._push(compose_buf); t_direct = utime.ticks_diff(utime.ticks_us(), t0)
print("RESULT per_reel_parts_62M: two_reads_and_blits_us=%d compose_to_fb_us=%d show_rect_us=%d direct_push_us=%d" % (t_comp, t_copy, t_rect, t_direct))
run("3_reels_as_described_62M", WIN_X)
run("3_reels_direct_push_62M", WIN_X, copy=False)
run("1_reel_as_described_62M", WIN_X[2:])
# DR-021 blink: gold frame on/off around the three windows, pushed as three windows
ts = []
for i in range(12):
    c = rgb(240, 200, 60) if i & 1 else rgb(40, 20, 10)
    t0 = utime.ticks_us()
    for x in WIN_X:
        lcd.rect(x - 2, WIN_Y - 2, S + 4, WIN_Y and S + 4, c)
        lcd.show_rect(x - 2, WIN_Y - 2, S + 4, S + 4, assets.scratch)
    ts.append(utime.ticks_diff(utime.ticks_us(), t0))
print("RESULT blink_3_windows_60x60: mean_us=%d max_us=%d" % (sum(ts) // 12, max(ts)))
# as shipped: clk_peri back on the USB PLL (48 MHz) -> the same SPI object now runs at 24 MHz
CTRL = 0x40008048; v = machine.mem32[CTRL]
machine.mem32[CTRL] = v & ~(1 << 11); utime.sleep_us(10)
machine.mem32[CTRL] = (v & ~(7 << 5)) | (2 << 5) & ~(1 << 11)
machine.mem32[CTRL] = (v & ~(7 << 5)) | (2 << 5) | (1 << 11); utime.sleep_us(10)
t0 = utime.ticks_us(); lcd.show(); t_full = utime.ticks_diff(utime.ticks_us(), t0)
print("RESULT clock_now=%s full_frame_us=%d (46 ms confirms 24 MHz)" % ('fast' if is_fast() else 'usb_pll_48MHz', t_full))
run("3_reels_as_described_24M", WIN_X)
run("3_reels_direct_push_24M", WIN_X, copy=False)
fast_peripherals()                                       # restore the state found (fixed)
t0 = utime.ticks_us(); lcd.show(); print("RESULT clock_restored=%s full_frame_us=%d" % (is_fast(), utime.ticks_diff(utime.ticks_us(), t0)))
gc.collect(); print("RESULT end mem_free=%d" % gc.mem_free())
os.remove('/assets/_bench_sym0.565'); os.remove('/assets/_bench_sym1.565')
print("RESULT cleanup assets=%s" % os.listdir('/assets'))
lcd.fill(0); lcd.show()
