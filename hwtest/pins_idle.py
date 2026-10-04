# pins_idle.py: READ-ONLY. All input pins from the pin map with pull-ups, read 200x at idle.
# Each should be solid 1 (nobody pressing). A 0 or a flicker means a short, a stuck key or a
# wrong pin. Also reads VSYS on ADC3 (GPIO29) via the Pico's 3:1 divider, which is a safe read.
from machine import Pin, ADC
import utime
names = {15:'A',17:'B',19:'X',21:'Y',2:'up',18:'down',16:'left',20:'right',3:'press'}
pins = {g: Pin(g, Pin.IN, Pin.PULL_UP) for g in names}
counts = {g: 0 for g in names}
for _ in range(200):
    for g, p in pins.items(): counts[g] += p.value()
    utime.sleep_ms(2)
print("RESULT idle_high_of_200: " + " ".join("%s(GP%d)=%d" % (names[g], g, counts[g]) for g in names))
a = ADC(29); v = [a.read_u16() for _ in range(32)]
print("RESULT vsys_adc29_mean_u16=%d approx_V=%.2f (x3 divider, 3.3 ref)" % (sum(v)//32, sum(v)/32/65535*3.3*3))
