# pins_reserved.py: READ-ONLY look at the RP2040-Plus pins the Pico reserves (23 power-save, 24 VBUS
# sense, 25 LED, 29 VSYS/3) plus the unused 0,1,4-7,14,22,26-28. Each is read as an input with the
# pull-up, then with the pull-down: a pin that reads the same both ways is driven by something on the
# board (or tied); one that follows the pull is floating/free. ADC pins are also sampled. Nothing is
# driven as an output (an LED test on GPIO25 would need a ruling first).
from machine import Pin, ADC
import utime
pins = (0, 1, 4, 5, 6, 7, 14, 22, 23, 24, 25, 26, 27, 28, 29)
for g in pins:
    up = Pin(g, Pin.IN, Pin.PULL_UP); utime.sleep_ms(5); u = sum(up.value() for _ in range(20))
    dn = Pin(g, Pin.IN, Pin.PULL_DOWN); utime.sleep_ms(5); d = sum(dn.value() for _ in range(20))
    Pin(g, Pin.IN)   # leave floating, no pull
    verdict = 'follows pull: floating/free' if (u == 20 and d == 0) else ('held HIGH externally' if (u == 20 and d == 20) else ('held LOW externally' if (u == 0 and d == 0) else 'mixed/unstable (%d/%d)' % (u, d)))
    extra = ''
    if g in (26, 27, 28, 29):
        a = ADC(g); v = sum(a.read_u16() for _ in range(32)) / 32
        extra = '  ADC%d=%.3f V (no pull)' % (g - 26, v / 65535 * 3.3)
    print("RESULT GP%-2d pullup=%2d/20 pulldown=%2d/20 -> %s%s" % (g, u, d, verdict, extra))
