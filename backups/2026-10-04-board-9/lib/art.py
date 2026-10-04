# Image loader for .565 files. Named art.py, not assets.py: on the board the /assets FOLDER would
# shadow a module called assets (HR-F02; '' is first on sys.path and a bare folder is a package).
# (ruling DR-002): 4-byte header (width, height, 16-bit little-endian)
# then big-endian RGB565 pixels, copied into framebuffers unchanged (DR-003).
# Ruling DR-005 / HR-005: one preallocated 16 KB scratch for every sprite; backgrounds read with one
# readinto straight into the framebuffer, on scene entry only, never per frame; big reads.
# Every loader returns False instead of raising when a file is missing or malformed, so the game
# falls back to code-drawn shapes while John's art is unfinished (DR-006).
# HR-F03: os.stat and the header read cost ~4-5 ms per call on LittleFS, so the size check runs
# once per asset per boot and is cached; later opens go straight to the pixels.

import framebuf
import os

from pixfmt import KEY
import sheets

HDR = 4
SCRATCH = 16384      # the logo (200 x 40 x 2 = 16,000) is the largest sprite


class Sheet:
    """An open sprite sheet (DR-024): one file, sprites of one size stacked vertically."""

    def __init__(self, name, f, scratch):
        self.name = name
        self.f = f
        self.w, self.h, self.names = sheets.SHEETS[name]
        self.n = self.w * self.h * 2
        self.scratch = scratch

    def read(self, index, buf):
        """Whole sprite `index` into buf (at least w*h*2 bytes). Returns True if read."""
        f = self.f
        f.seek(sheets.offset(self.name, index))
        return f.readinto(memoryview(buf)[:self.n]) == self.n

    def rows(self, index, first, count, dst):
        """Rows first..first+count-1 of sprite `index` into dst (count * w * 2 bytes)."""
        row = self.w * 2
        self.f.seek(sheets.offset(self.name, index) + first * row)
        return self.f.readinto(memoryview(dst)[:count * row]) == count * row

    def blit(self, fb, index, x, y, key=KEY):
        if not self.read(index, self.scratch):
            return False
        spr = framebuf.FrameBuffer(memoryview(self.scratch)[:self.n], self.w, self.h, framebuf.RGB565)
        fb.blit(spr, x, y, key)
        return True

    def close(self):
        if self.f is not None:
            self.f.close()
            self.f = None


class Assets:
    def __init__(self, root='/assets', scratch_size=SCRATCH):
        self.root = root
        self.scratch = bytearray(scratch_size)
        self.hdr = bytearray(HDR)
        self.missing = {}        # names we failed to open, so we don't retry every draw
        self.known = {}          # name -> (w, h) once the file has passed the length check (HR-F03)
        self.open_sheets = {}    # sheet name -> Sheet, while a scene has them open (DR-024)

    # ---- sheets (DR-024) ----------------------------------------------------------------------
    def sheet(self, name):
        """Open sheet `name` (validated: a tall image of count x sprite height). None if absent.
        The caller closes it, or uses use_sheets()/release_sheets()."""
        if name not in sheets.SHEETS:
            return None
        r = self._open(name)
        if r is None:
            return None
        f, w, h = r
        sw, sh, names = sheets.SHEETS[name]
        if w != sw or h != sh * len(names):
            f.close()
            self.missing[name] = 1
            return None
        return Sheet(name, f, self.scratch)

    def use_sheets(self, names):
        """Open these sheets for the scene; blit()/load() then draw members from them."""
        for n in names:
            if n not in self.open_sheets:
                s = self.sheet(n)
                if s is not None:
                    self.open_sheets[n] = s

    def release_sheets(self):
        for s in self.open_sheets.values():
            s.close()
        self.open_sheets = {}

    def _from_sheet(self, name):
        """(Sheet, index) if `name` is a member of an open sheet."""
        m = sheets.member(name)
        if m is None:
            return None
        s = self.open_sheets.get(m[0])
        if s is None:
            return None
        return s, m[1]

    def path(self, name):
        return self.root + '/' + name + '.565'

    def _open(self, name):
        """Open and validate; return (file, w, h) positioned at the first pixel, or None."""
        if name in self.missing:
            return None
        known = self.known.get(name)
        if known is not None:
            try:
                f = open(self.path(name), 'rb')
                f.seek(HDR)
            except OSError:
                del self.known[name]
                self.missing[name] = 1
                return None
            return f, known[0], known[1]
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
        self.known[name] = (w, h)
        return f, w, h

    def load(self, name, buf):
        """Read a sprite's pixels into `buf` (a bytearray or memoryview of at least w*h*2 bytes),
        for callers that keep sprites in RAM (slots, HR-020). Returns (w, h) or None."""
        fs = self._from_sheet(name)
        if fs is not None:
            s, i = fs
            if s.n <= len(buf) and s.read(i, buf):
                return s.w, s.h
            return None
        r = self._open(name)
        if r is None:
            return None
        f, w, h = r
        n = w * h * 2
        if n > len(buf):
            f.close()
            return None
        ok = f.readinto(memoryview(buf)[:n]) == n
        f.close()
        return (w, h) if ok else None

    def open_sprite(self, name):
        """Open a validated sprite positioned at its first pixel: (file, w, h) or None. The caller
        reads rows with seek/readinto and must close it. For animations that stream a symbol in
        over several frames (slots, HR-020) without re-opening per frame."""
        return self._open(name)

    def size(self, name):
        r = self._open(name)
        if r is None:
            return None
        r[0].close()
        return r[1], r[2]

    def blit(self, fb, name, x, y, key=KEY):
        """Draw sprite `name` at (x, y) with magenta transparent. Returns True if drawn.
        From an open sheet when the name is a member of one (DR-024), else from its own file."""
        fs = self._from_sheet(name)
        if fs is not None:
            return fs[0].blit(fb, fs[1], x, y, key)
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
