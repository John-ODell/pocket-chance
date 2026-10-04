# Shared bench driver (hwtest only). Same pins/init sequence as main_monolith.py, with
# window writes added so partial pushes can be timed. Not for the dev to import.
from machine import Pin, SPI, PWM
import framebuf, utime

BL, DC, RST, MOSI, SCK, CS = 13, 8, 12, 11, 10, 9

def spi_baud(spi):
    # repr looks like SPI(1, baudrate=62500000, polarity=0, ...); read the granted value
    s = repr(spi)
    i = s.find('baudrate=')
    if i < 0:
        return None
    j = i + 9
    k = j
    while k < len(s) and s[k].isdigit():
        k += 1
    return int(s[j:k])

class Bench:
    def __init__(self, baud=100_000_000, fb=True):
        self.cs = Pin(CS, Pin.OUT, value=1)
        self.rst = Pin(RST, Pin.OUT, value=1)
        self.dc = Pin(DC, Pin.OUT, value=1)
        self.requested = baud
        self.spi = SPI(1, baud, polarity=0, phase=0, sck=Pin(SCK), mosi=Pin(MOSI), miso=None)
        self.granted = spi_baud(self.spi)
        self.pwm = PWM(Pin(BL)); self.pwm.freq(1000); self.pwm.duty_u16(20000)
        self.buf = bytearray(240 * 240 * 2) if fb else None
        self.fb = framebuf.FrameBuffer(self.buf, 240, 240, framebuf.RGB565) if fb else None
        self._init()

    def cmd(self, c, data=None):
        self.cs(1); self.dc(0); self.cs(0)
        self.spi.write(bytes([c]))
        if data is not None:
            self.dc(1)
            self.spi.write(data)
        self.cs(1)

    def _init(self):
        self.rst(1); self.rst(0); utime.sleep_ms(10); self.rst(1); utime.sleep_ms(120)
        for c, d in ((0x36, b'\x70'), (0x3A, b'\x05'), (0xB2, b'\x0c\x0c\x00\x33\x33'),
                     (0xB7, b'\x35'), (0xBB, b'\x19'), (0xC0, b'\x2c'), (0xC2, b'\x01'),
                     (0xC3, b'\x12'), (0xC4, b'\x20'), (0xC6, b'\x0f'), (0xD0, b'\xa4\xa1'),
                     (0xE0, b'\xd0\x04\x0d\x11\x13\x2b\x3f\x54\x4c\x18\x0d\x0b\x1f\x23'),
                     (0xE1, b'\xd0\x04\x0c\x11\x13\x2c\x3f\x44\x51\x2f\x1f\x1f\x20\x23')):
            self.cmd(c, d)
        self.cmd(0x21); self.cmd(0x11); utime.sleep_ms(120); self.cmd(0x29)

    def window(self, x, y, w, h):
        x1 = x + w - 1; y1 = y + h - 1
        self.cmd(0x2A, bytes([x >> 8, x & 255, x1 >> 8, x1 & 255]))
        self.cmd(0x2B, bytes([y >> 8, y & 255, y1 >> 8, y1 & 255]))
        self.cmd(0x2C)

    def push(self, data):
        # data already written after RAMWR; stream it
        self.cs(1); self.dc(1); self.cs(0)
        self.spi.write(data)
        self.cs(1)

    def show(self):
        self.window(0, 0, 240, 240)
        self.push(self.buf)

    def blank(self):
        self.fb.fill(0); self.show()

def stats(name, times_us, unit_frames=1):
    n = len(times_us)
    tot = sum(times_us)
    mean = tot / n
    print("RESULT %s_mean_us=%d min_us=%d max_us=%d n=%d fps=%.1f" %
          (name, mean, min(times_us), max(times_us), n, 1e6 / mean * unit_frames))
