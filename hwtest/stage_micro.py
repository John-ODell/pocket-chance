# stage_micro.py: why did step 1i's blackjack timing move? Times sheets.member(), a card blit on the
# miss path (no sheet), then writes a temporary full cards.565 (non-magenta, so every card is
# "present") and times a card blit from the sheet and pocket_bench's redraw paths with it; removes it.
import sys, gc, utime, os
sys.path.insert(0, '/remote/stage')
import sheets, art
from clocks import fast_peripherals; fast_peripherals()
from lcd import LCD
lcd = LCD(62_500_000); gc.collect()
from pixfmt import KEY
t0 = utime.ticks_us()
for _ in range(100): sheets.member('c_AS')
print("RESULT sheets.member_us=%.1f (per call, 100 calls)" % (utime.ticks_diff(utime.ticks_us(), t0) / 100))
a = art.Assets('/assets')
if hasattr(a, 'use_sheets'): a.use_sheets(('cards', 'chips', 'banners'))
ts = []
for _ in range(5):
    t0 = utime.ticks_us(); a.blit(lcd, 'c_AS', 10, 10); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
print("RESULT card_blit_MISS_us first=%d then=%s (no sheet, no file: this is what a code-drawn card pays before drawing)" % (ts[0], ts[1:]))
# temp full card sheet, every card present (pattern 0x1234, corners not magenta either)
W, H, N = 40, 56, 53
t0 = utime.ticks_ms()
with open('/assets/cards.565', 'wb') as f:
    f.write(bytes([W & 255, W >> 8, (H * N) & 255, (H * N) >> 8]))
    row = bytes([0x12, 0x34]) * W
    for k in range(N):
        for y in range(H): f.write(row)
print("RESULT wrote temp cards.565 %d B in %d ms" % (os.stat('/assets/cards.565')[6], utime.ticks_diff(utime.ticks_ms(), t0)))
a = art.Assets('/assets')
if hasattr(a, 'use_sheets'): a.use_sheets(('cards',))
ts = []
for n in ('c_AS', 'c_KH', 'c_7D', 'c_back', 'c_2C'):
    t0 = utime.ticks_us(); ok = a.blit(lcd, n, 10, 10); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
print("RESULT card_blit_from_SHEET_us=%s ok=%s" % (ts, ok))
if hasattr(a, 'release_sheets'): a.release_sheets()
lcd.fill(0); lcd.show()
