# Image loader for .565 files (ruling DR-002): 4-byte header (width, height, 16-bit little-endian)
# then big-endian RGB565 pixels, copied into framebuffers unchanged (DR-003).
# Ruling DR-005 / HR-005: one preallocated 16 KB scratch for every sprite; backgrounds read with one
# readinto straight into the framebuffer, on scene entry only, never per frame; big reads.
# Every loader returns False instead of raising when a file is missing or malformed, so the game
# falls back to code-drawn shapes while John's art is unfinished (DR-006).

import framebuf
import os

from pixfmt import KEY

HDR = 4
SCRATCH = 16384      # the logo (200 x 40 x 2 = 16,000) is the largest sprite


class Assets:
    def __init__(self, root='/assets', scratch_size=SCRATCH):
        self.root = root
        self.scratch = bytearray(scratch_size)
        self.hdr = bytearray(HDR)
        self.missing = {}        # names we failed to open, so we don't retry every draw

    def path(self, name):
        return self.root + '/' + name + '.565'

    def _open(self, name):
        """Open and validate; return (file, w, h) or None."""
        if name in self.missing:
            return None
        try:
            p = self.path(name)
            size = os.stat(p)[6]
            f = open(p, 'rb')
        except OSError:
            self.missing[name] = 1
            return None
        hdr = self.hdr
        if f.readinto(hdr) != HDR:
            f.close()
            self.missing[name] = 1
            return None
        w = hdr[0] | (hdr[1] << 8)
        h = hdr[2] | (hdr[3] << 8)
        if w == 0 or h == 0 or size != HDR + w * h * 2:
            f.close()
            self.missing[name] = 1
            return None
        return f, w, h

    def size(self, name):
        r = self._open(name)
        if r is None:
            return None
        r[0].close()
        return r[1], r[2]

    def blit(self, fb, name, x, y, key=KEY):
        """Draw sprite `name` at (x, y) with magenta transparent. Returns True if drawn."""
        r = self._open(name)
        if r is None:
            return False
        f, w, h = r
        n = w * h * 2
        if n > len(self.scratch):
            f.close()
            return False
        mv = memoryview(self.scratch)[:n]
        ok = f.readinto(mv) == n
        f.close()
        if not ok:
            return False
        spr = framebuf.FrameBuffer(mv, w, h, framebuf.RGB565)
        fb.blit(spr, x, y, key)
        return True

    def background(self, lcd, name):
        """Read a full-screen image straight into the LCD's framebuffer (one read, ~21 ms)."""
        r = self._open(name)
        if r is None:
            return False
        f, w, h = r
        if w != lcd.width or h != lcd.height:
            f.close()
            return False
        buf = lcd.buffer
        ok = f.readinto(buf) == len(buf)
        f.close()
        return ok

    def background_rows(self, lcd, name, y, h):
        """Restore rows y..y+h-1 of a full-screen image into the framebuffer (for band redraws)."""
        r = self._open(name)
        if r is None:
            return False
        f, w, hh = r
        if w != lcd.width or hh != lcd.height or y < 0 or y + h > hh:
            f.close()
            return False
        row = w * 2
        f.seek(HDR + y * row)
        mv = memoryview(lcd.buffer)[y * row:(y + h) * row]
        ok = f.readinto(mv) == h * row
        f.close()
        return ok
