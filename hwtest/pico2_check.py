# pico2_check.py: for a Raspberry Pi Pico 2 (RP2350) with the Waveshare 1.3" HAT fitted. READ-ONLY on
# registers: it never pokes CLK_PERI_CTRL (lib/clocks.py and clk_peri_fix.py are RP2040-only and must
# NOT be run on an RP2350). Uses machine.freq(mcu, peripheral) only. Reports: firmware, clock, flash,
# RAM, the clk_peri source at the RP2350 address (CLOCKS_BASE 0x40010000 + 0x48, confirm in the
# datasheet), the SPI(1) baud granted for a 62.5 MHz request and the timed full frame in three states:
# as shipped; machine.freq(125M, 125M); machine.freq(150M, 150M). Restores the shipped clocks at the end.
import os, sys, gc, machine, utime
from machine import SPI, Pin
u = os.uname(); print("RESULT %s %s %s" % (u.sysname, u.release, u.machine))
print("RESULT impl=%s" % (sys.implementation,))
vfs = os.statvfs('/'); print("RESULT cpu_hz=%d fs_total=%d" % (machine.freq(), vfs[0] * vfs[2]))
gc.collect(); print("RESULT ram_free_boot=%d" % gc.mem_free())
CTRL = 0x40010048                      # RP2350 CLOCKS.CLK_PERI_CTRL (PCB maker, from the SDK addressmap; verify)
SRC = {0: 'clk_sys', 1: 'pll_sys', 2: 'pll_usb(48MHz)', 3: 'rosc', 4: 'xosc'}
def state():
    v = machine.mem32[CTRL]; return "CLK_PERI_CTRL=0x%08x auxsrc=%s" % (v, SRC.get((v >> 5) & 7, '?'))
def spi_repr():
    s = SPI(1, 62_500_000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11), miso=None)
    r = repr(s); i = r.find('baudrate=') + 9; j = i
    while r[j].isdigit(): j += 1
    s.deinit(); return int(r[i:j])
def frame():
    from lcdbench import Bench
    b = Bench(baud=62_500_000); ts = []
    for i in range(30):
        b.fb.fill((0xF800, 0x07E0, 0x001F, 0xFFFF)[i & 3]); t0 = utime.ticks_us(); b.show(); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
    b.blank(); b.spi.deinit(); return sum(ts) // 30
shipped = machine.freq()
print("RESULT as_shipped: freq=%d %s spi_repr=%d full_frame_us=%d" % (machine.freq(), state(), spi_repr(), frame()))
for mcu in (125_000_000, 150_000_000):
    try:
        machine.freq(mcu, mcu)
        print("RESULT after freq(%d,%d): %s spi_repr=%d full_frame_us=%d" % (mcu, mcu, state(), spi_repr(), frame()))
    except Exception as e:
        print("RESULT freq(%d,%d) failed: %r" % (mcu, mcu, e))
machine.freq(shipped, 48_000_000)
gc.collect(); print("RESULT restored: freq=%d %s ram_free=%d" % (machine.freq(), state(), gc.mem_free()))
print("RESULT look at the panel: four solid colours cycled in each state; speckles or tearing = that SPI speed is not clean on this wiring")
