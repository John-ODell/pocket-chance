# Fake `framebuf` for CPython tests: a real RGB565 pixel store with the methods the game uses.
# Semantics follow MicroPython's (little-endian 16-bit pixels, blit skips `key`, clipping).

RGB565 = 1


class FrameBuffer:
    def __init__(self, buf, width, height, fmt, stride=None):
        if fmt != RGB565:
            raise ValueError('fake only supports RGB565')
        if len(buf) < width * height * 2:
            raise ValueError('buffer too small')
        self.buf = buf
        self.w = width
        self.h = height

    def _idx(self, x, y):
        return (y * self.w + x) * 2

    def pixel(self, x, y, c=None):
        if not (0 <= x < self.w and 0 <= y < self.h):
            return None if c is None else None
        i = self._idx(x, y)
        if c is None:
            return self.buf[i] | (self.buf[i + 1] << 8)
        self.buf[i] = c & 0xFF
        self.buf[i + 1] = (c >> 8) & 0xFF

    def fill(self, c):
        self.fill_rect(0, 0, self.w, self.h, c)

    def fill_rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        lo = c & 0xFF
        hi = (c >> 8) & 0xFF
        for yy in range(y0, y1):
            i = self._idx(x0, yy)
            for _ in range(x1 - x0):
                self.buf[i] = lo
                self.buf[i + 1] = hi
                i += 2

    def rect(self, x, y, w, h, c, f=False):
        if f:
            self.fill_rect(x, y, w, h, c)
            return
        self.hline(x, y, w, c)
        self.hline(x, y + h - 1, w, c)
        self.vline(x, y, h, c)
        self.vline(x + w - 1, y, h, c)

    def hline(self, x, y, w, c):
        self.fill_rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.fill_rect(x, y, 1, h, c)

    def line(self, x0, y0, x1, y1, c):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(steps + 1):
            self.pixel(x0 + (x1 - x0) * i // steps, y0 + (y1 - y0) * i // steps, c)

    def ellipse(self, cx, cy, xr, yr, c, f=False, m=0xF):
        for y in range(-yr, yr + 1):
            for x in range(-xr, xr + 1):
                d = (x * x) / float(xr * xr or 1) + (y * y) / float(yr * yr or 1)
                if d <= 1.0 and (f or d > 0.75):
                    self.pixel(cx + x, cy + y, c)

    def text(self, s, x, y, c=1):
        # a stand-in glyph: a diagonal plus the top row, 8x8 cell per character
        for ch in s:
            for i in range(8):
                self.pixel(x + i, y + i, c)
                self.pixel(x + i, y, c)
            x += 8

    def blit(self, fb, x, y, key=-1, palette=None):
        for yy in range(fb.h):
            for xx in range(fb.w):
                p = fb.pixel(xx, yy)
                if p != key:
                    self.pixel(x + xx, y + yy, p)

    def scroll(self, dx, dy):
        pass
