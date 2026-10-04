# Pilot board test (DR-006). Run it on the board from Viper IDE WITHOUT saving it. It needs /lib
# uploaded (see UPLOAD.md) and whatever pilot images are in /assets. Draws the table, two cards and a
# chip with code-drawn fallbacks for anything missing, and prints RESULT lines for the expert:
# which images loaded, free RAM, and how long a background read, a sprite blit and a show() take.
# Writes nothing to flash.

FAST_SPI = True

import sys
import gc
import utime

if '/games' not in sys.path:
    sys.path.append('/games')
if FAST_SPI:
    from clocks import fast_peripherals
    print('RESULT clk_peri changed=%s' % fast_peripherals())

from lcd import LCD
lcd = LCD(62_500_000)
gc.collect()
print('RESULT after framebuffer mem_free=%d' % gc.mem_free())

import font
from pixfmt import rgb
from art import Assets

a = Assets('/assets')
for name in ('table', 'c_AS', 'c_back', 'chip_5', 'logo'):
    print('RESULT asset %s size=%s' % (name, a.size(name)))

t = utime.ticks_us()
ok = a.background(lcd, 'table')
print('RESULT background loaded=%s us=%d' % (ok, utime.ticks_diff(utime.ticks_us(), t)))
if not ok:
    lcd.fill(rgb(0, 90, 40))

t = utime.ticks_us()
ok1 = a.blit(lcd, 'c_AS', 60, 60)
t1 = utime.ticks_diff(utime.ticks_us(), t)
t = utime.ticks_us()
ok2 = a.blit(lcd, 'c_back', 140, 60)
t2 = utime.ticks_diff(utime.ticks_us(), t)
ok3 = a.blit(lcd, 'chip_5', 108, 140)
print('RESULT blit c_AS=%s us=%d  c_back=%s us=%d  chip_5=%s' % (ok1, t1, ok2, t2, ok3))
if not ok1:
    lcd.fill_rect(60, 60, 40, 56, rgb(240, 232, 200))
    font.text(lcd, 'A', 64, 64, rgb(0, 0, 0), 2)
if not ok2:
    lcd.fill_rect(140, 60, 40, 56, rgb(30, 60, 160))
if not ok3:
    lcd.ellipse(119, 151, 11, 11, rgb(200, 20, 20), True)

font.text_centred(lcd, 'PILOT TEST', 120, 12, rgb(240, 200, 60), 2)
font.text(lcd, 'TOP-LEFT', 2, 230, rgb(255, 255, 255), 1)

t = utime.ticks_us()
lcd.show()
print('RESULT show us=%d' % utime.ticks_diff(utime.ticks_us(), t))
t = utime.ticks_us()
lcd.show_band(0, 48)
print('RESULT band48 us=%d' % utime.ticks_diff(utime.ticks_us(), t))
gc.collect()
print('RESULT end mem_free=%d' % gc.mem_free())
print('RESULT done. Expect: ace and card back side by side, red chip below, title on top, text bottom-left.')
