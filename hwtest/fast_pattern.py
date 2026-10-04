# fast_pattern.py: VISUAL check of the panel at the real 62.5 MHz on v1.29.0. Applies the clk_peri
# fix (same writes as clk_peri_fix.py), then draws a demanding static pattern: fine 1-px checker
# bands, colour bars, text, a 1-px white border. Any SPI error at this speed shows as speckles,
# shifted rows or wrong colours. Times 100 frames to prove the speed, leaves the pattern on screen.
# The register change is cleared by a power cycle.
import machine, utime
CTRL = 0x40008048
v = machine.mem32[CTRL]
if (v >> 5) & 7 != 0:
    machine.mem32[CTRL] = v & ~(1 << 11); utime.sleep_us(10)
    machine.mem32[CTRL] = (v & ~(7 << 5)) & ~(1 << 11)
    machine.mem32[CTRL] = (v & ~(7 << 5)) | (1 << 11); utime.sleep_us(10)
from lcdbench import Bench
b = Bench(baud=62_500_000)
fb = b.fb
bars = (0x00F8, 0xE007, 0x1F00, 0xE0FF, 0xFF07, 0x1FF8, 0xFFFF, 0x0000)  # byte-swapped R G B Y C M W K
for i, c in enumerate(bars):
    fb.fill_rect(i * 30, 0, 30, 80, c)
for y in range(80, 140):
    for x in range(0, 240, 2):
        fb.pixel(x + (y & 1), y, 0xFFFF)   # 1-px checkerboard
fb.fill_rect(0, 140, 240, 100, 0x0000)
for k in range(8):
    fb.text("62.5 MHz check line %d" % k, 4, 144 + k * 11, 0xFFFF)
fb.rect(0, 0, 240, 240, 0xFFFF)
ts = []
for _ in range(100):
    t = utime.ticks_us(); b.show(); ts.append(utime.ticks_diff(utime.ticks_us(), t))
print("RESULT fast_pattern frame_us_mean=%d fps=%.1f CLK_PERI_CTRL=0x%08x" % (sum(ts) // 100, 1e8 / sum(ts), machine.mem32[CTRL]))
print("RESULT ask John: 8 clean colour bars (red green blue yellow cyan magenta white black), a fine grey-looking checker band, 8 lines of crisp text, 1-px white border; any speckles, tearing or shifted rows?")
