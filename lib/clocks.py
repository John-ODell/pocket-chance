# Peripheral clock fix (ruling DR-015, measured in hw/reviews/HR-015.md).
#
# MicroPython v1.29.0 feeds clk_peri from the 48 MHz USB PLL, which caps SPI at 24 MHz. Re-sourcing
# it from the 125 MHz system clock lets SPI run at 62.5 MHz (full frame 17 ms instead of 46 ms).
# RP2040 datasheet 2.15.3.2: clk_peri has only an aux mux, so disable, set AUXSRC, enable.
# Only SPI and UART baud generation depend on clk_peri; USB, PWM, I2C and the CPU do not.
#
# Call fast_peripherals() BEFORE creating the SPI object. MicroPython caches the clock it believes
# clk_peri has, so after the fix every requested SPI baud is really 125/48 = 2.6x what the repr
# prints: request 62_500_000 for a real 62.5 MHz, or 12_000_000 for a real 31.25 MHz (HR-015).
# Off switch: FAST_SPI in pocket.py. Safe to call twice; a soft reset keeps the fast state and an
# unplug returns the shipped state, and both end up the same after this runs.

import machine
import utime

CTRL = 0x40008048        # CLOCKS.CLK_PERI_CTRL
ENABLE = 1 << 11
AUXSRC = 7 << 5          # 0 = clk_sys


def fast_peripherals():
    """Point clk_peri at clk_sys. Returns True if it changed anything."""
    v = machine.mem32[CTRL]
    if v & AUXSRC == 0:
        return False
    machine.mem32[CTRL] = v & ~ENABLE
    utime.sleep_us(10)
    machine.mem32[CTRL] = v & ~ENABLE & ~AUXSRC
    machine.mem32[CTRL] = (v & ~AUXSRC) | ENABLE
    utime.sleep_us(10)
    return True


def is_fast():
    return machine.mem32[CTRL] & AUXSRC == 0
