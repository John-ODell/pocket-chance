# ST7789 driver for the Waveshare Pico LCD 1.3" (240x240), with window pushes for partial redraws.
# Init sequence and pins from main_monolith.py (Tony Goodhew, 2021) and hwtest/lcdbench.py.
# Rulings: DR-003 (0x36 = 0x70 gives upright landscape, framebuf (0,0) is the player's top-left),
# DR-005 (push bands, full show() only on scene change), DR-015 (create after fast_peripherals()).

from machine import Pin, SPI, PWM
import framebuf
import utime

BL, DC, RST, MOSI, SCK, CS = 13, 8, 12, 11, 10, 9
WIDTH = 240
HEIGHT = 240
ROW_BYTES = WIDTH * 2

_INIT = (
    (0x36, b'\x70'), (0x3A, b'\x05'), (0xB2, b'\x0c\x0c\x00\x33\x33'),
    (0xB7, b'\x35'), (0xBB, b'\x19'), (0xC0, b'\x2c'), (0xC2, b'\x01'),
    (0xC3, b'\x12'), (0xC4, b'\x20'), (0xC6, b'\x0f'), (0xD0, b'\xa4\xa1'),
    (0xE0, b'\xd0\x04\x0d\x11\x13\x2b\x3f\x54\x4c\x18\x0d\x0b\x1f\x23'),
    (0xE1, b'\xd0\x04\x0c\x11\x13\x2c\x3f\x44\x51\x2f\x1f\x1f\x20\x23'),
)


class LCD(framebuf.FrameBuffer):
    """One 115,200-byte framebuffer. Create it first, before anything else large (HR-001)."""

    def __init__(self, baud=62_500_000, backlight=20000):
        self.width = WIDTH
        self.height = HEIGHT
        self.buffer = bytearray(HEIGHT * ROW_BYTES)
        super().__init__(self.buffer, WIDTH, HEIGHT, framebuf.RGB565)
        self.cs = Pin(CS, Pin.OUT, value=1)
        self.rst = Pin(RST, Pin.OUT, value=1)
        self.dc = Pin(DC, Pin.OUT, value=1)
        self.spi = SPI(1, baud, polarity=0, phase=0, sck=Pin(SCK), mosi=Pin(MOSI), miso=None)
        self.pwm = PWM(Pin(BL))
        self.pwm.freq(1000)
        self.pwm.duty_u16(backlight)
        self._win = bytearray(4)
        self._c = bytearray(1)
        self._init()

    def _cmd(self, c, data=None):
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self._c[0] = c
        self.spi.write(self._c)
        if data is not None:
            self.dc(1)
            self.spi.write(data)
        self.cs(1)

    def _init(self):
        self.rst(1)
        self.rst(0)
        utime.sleep_ms(10)
        self.rst(1)
        utime.sleep_ms(120)
        for c, d in _INIT:
            self._cmd(c, d)
        self._cmd(0x21)
        self._cmd(0x11)
        utime.sleep_ms(120)
        self._cmd(0x29)

    def backlight(self, level):
        """0 (off) to 65535 (full)."""
        self.pwm.duty_u16(level)

    def _window(self, x, y, w, h):
        win = self._win
        x1 = x + w - 1
        y1 = y + h - 1
        win[0] = x >> 8
        win[1] = x & 255
        win[2] = x1 >> 8
        win[3] = x1 & 255
        self._cmd(0x2A, win)
        win[0] = y >> 8
        win[1] = y & 255
        win[2] = y1 >> 8
        win[3] = y1 & 255
        self._cmd(0x2B, win)
        self._cmd(0x2C)

    def _push(self, data):
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(data)
        self.cs(1)

    def show(self):
        """Push the whole framebuffer (about 17 ms at 62.5 MHz, 46 ms at 24 MHz)."""
        self._window(0, 0, WIDTH, HEIGHT)
        self._push(self.buffer)

    def show_band(self, y, h):
        """Push full-width rows y..y+h-1 straight from the framebuffer. No copy, no allocation."""
        if y < 0:
            h += y
            y = 0
        if y + h > HEIGHT:
            h = HEIGHT - y
        if h <= 0:
            return
        self._window(0, y, WIDTH, h)
        self._push(memoryview(self.buffer)[y * ROW_BYTES:(y + h) * ROW_BYTES])

    def show_buf(self, x, y, w, h, buf):
        """Push a prepared w x h RGB565 buffer to a window of the panel, without touching the
        framebuffer (HR-020: a composed reel window goes straight to the panel, ~1.5 ms)."""
        self._window(x, y, w, h)
        n = w * h * 2
        self._push(buf if len(buf) == n else memoryview(buf)[:n])    # no slice object when it fits exactly

    def show_rect(self, x, y, w, h, scratch):
        """Push a window by copying its rows into `scratch` (needs w*h*2 bytes, else falls back
        to show_band). Worth it for small windows; a band is simpler for anything wide."""
        n = w * h * 2
        if n > len(scratch):
            self.show_band(y, h)
            return
        buf = self.buffer
        row = w * 2
        src = x * 2 + y * ROW_BYTES
        dst = 0
        for _ in range(h):
            scratch[dst:dst + row] = buf[src:src + row]
            src += ROW_BYTES
            dst += row
        self._window(x, y, w, h)
        self._push(memoryview(scratch)[:n])
