# clk_peri.py: why did SPI drop to 24 MHz on v1.29.0? Reads CLOCKS.CLK_PERI_CTRL (RP2040 datasheet
# 2.15.7: AUXSRC bits 7:5, 0=clk_sys 1=pll_sys 2=pll_usb 3=rosc 4=xosc; ENABLE bit 11), then tries
# the supported fix, machine.freq(current), which in MicroPython re-sources clk_peri from clk_sys,
# and re-measures the SPI baud the chip grants. Nothing is written except that one register via
# machine.freq(); a soft reset restores defaults.
import machine, utime
from machine import SPI, Pin
CTRL = 0x40008000 + 0x48
SRC = {0:'clk_sys', 1:'pll_sys', 2:'pll_usb(48MHz)', 3:'rosc', 4:'xosc(12MHz)', 5:'gpin0', 6:'gpin1'}
def ctrl():
    v = machine.mem32[CTRL]; return v, SRC.get((v >> 5) & 7, '?'), bool(v & (1 << 11))
def spi_baud():
    s = SPI(1, 62_500_000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11), miso=None)
    r = repr(s); i = r.find('baudrate=') + 9; j = i
    while r[j].isdigit(): j += 1
    s.deinit(); return int(r[i:j])
v, src, en = ctrl()
print("RESULT before: CLK_PERI_CTRL=0x%08x auxsrc=%s enabled=%s machine.freq=%d spi_granted=%d" % (v, src, en, machine.freq(), spi_baud()))
machine.freq(machine.freq())
v, src, en = ctrl()
print("RESULT after machine.freq(same): CLK_PERI_CTRL=0x%08x auxsrc=%s enabled=%s spi_granted=%d" % (v, src, en, spi_baud()))
