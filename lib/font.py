# Text drawing on a framebuf, using MicroPython's built-in 8x8 font scaled up by whole numbers.
# Size 1 is framebuf.text() itself. Larger sizes render each character into a tiny 8x8 scratch
# buffer (128 bytes, allocated once) and draw each lit pixel as a size x size block.
# Per-character cost grows with size; draw text on input, not every frame.

import framebuf

CH = 8   # built-in glyph cell, pixels

_buf = bytearray(CH * CH * 2)
_glyph = framebuf.FrameBuffer(_buf, CH, CH, framebuf.RGB565)


def width(s, size=1):
    return len(s) * CH * size


def text(fb, s, x, y, c, size=1):
    """Draw string s with its top-left corner at (x, y)."""
    if size <= 1:
        fb.text(s, x, y, c)
        return
    g = _glyph
    step = CH * size
    for ch in s:
        g.fill(0)
        g.text(ch, 0, 0, 1)
        for gy in range(CH):
            yy = y + gy * size
            for gx in range(CH):
                if g.pixel(gx, gy):
                    fb.fill_rect(x + gx * size, yy, size, size, c)
        x += step


def text_centred(fb, s, cx, y, c, size=1):
    text(fb, s, cx - width(s, size) // 2, y, c, size)


def text_right(fb, s, right, y, c, size=1):
    text(fb, s, right - width(s, size), y, c, size)
