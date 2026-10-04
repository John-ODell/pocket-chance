# freq_peri.py: HR-F05. Does machine.freq(mcu, peripheral) replace the CLK_PERI_CTRL poke in
# lib/clocks.py? Measures, in order: the state found; machine.freq(125_000_000, 125_000_000) (or the
# v1.29.0 signature, probed first); the register, the SPI baud MicroPython now REPORTS (is the repr
# honest?), a timed full frame (the truth), backlight PWM frequency, then restores the state found.
# Read-only except the clock settings, which a power cycle also resets.
import machine, utime, gc
from machine import SPI, Pin, PWM
CTRL = 0x40008048
SRC = {0: 'clk_sys', 1: 'pll_sys', 2: 'pll_usb(48MHz)', 3: 'rosc', 4: 'xosc'}
def state():
    v = machine.mem32[CTRL]; return "CLK_PERI_CTRL=0x%08x auxsrc=%s" % (v, SRC.get((v >> 5) & 7, '?'))
def spi_repr_baud():
    s = SPI(1, 62_500_000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11), miso=None)
    r = repr(s); i = r.find('baudrate=') + 9; j = i
    while r[j].isdigit(): j += 1
    s.deinit(); return int(r[i:j])
def frame_us():
    from lcd import LCD
    l = LCD(62_500_000); l.fill(0x07E0); l.show()
    ts = []
    for i in range(30):
        l.fill((0xF800, 0x07E0, 0x001F, 0xFFFF)[i & 3]); t0 = utime.ticks_us(); l.show(); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
    pwm_f = l.pwm.freq(); l.fill(0); l.show(); l.spi.deinit()
    return sum(ts) // 30, pwm_f
found = machine.mem32[CTRL]
print("RESULT found: %s machine.freq=%d" % (state(), machine.freq()))
print("RESULT found: spi_repr_baud=%d" % spi_repr_baud())
f, p = frame_us(); print("RESULT found: full_frame_us=%d backlight_pwm_hz=%d" % (f, p))
# signature probe
try:
    machine.freq(125_000_000, 125_000_000); sig = 'machine.freq(mcu, peripheral) accepted'
except TypeError as e:
    sig = 'two-arg form rejected: %r' % (e,)
print("RESULT signature: %s; machine.freq()=%d" % (sig, machine.freq()))
print("RESULT after freq(125M,125M): %s" % state())
print("RESULT after freq(125M,125M): spi_repr_baud=%d" % spi_repr_baud())
f, p = frame_us(); print("RESULT after freq(125M,125M): full_frame_us=%d backlight_pwm_hz=%d (17-19 ms = real 62.5 MHz)" % (f, p))
# and back to the documented default
try:
    machine.freq(125_000_000, 48_000_000)
    print("RESULT after freq(125M,48M): %s spi_repr_baud=%d" % (state(), spi_repr_baud()))
    f, p = frame_us(); print("RESULT after freq(125M,48M): full_frame_us=%d (46 ms = 24 MHz)" % f)
except TypeError as e:
    print("RESULT freq(125M,48M) rejected: %r" % (e,))
# restore what was found
v = machine.mem32[CTRL]
if v != found:
    machine.mem32[CTRL] = v & ~(1 << 11); utime.sleep_us(10)
    machine.mem32[CTRL] = (found & ~(1 << 11)); machine.mem32[CTRL] = found; utime.sleep_us(10)
print("RESULT restored: %s (found 0x%08x)" % (state(), found))
gc.collect(); print("RESULT usb_still_up=yes (this line arrived) mem_free=%d" % gc.mem_free())
