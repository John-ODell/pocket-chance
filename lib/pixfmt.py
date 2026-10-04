# Pixel format helpers shared by the board code and the Mac-side converter. Pure: no `machine`.
#
# Ruling DR-003: the panel takes big-endian RGB565 and `framebuf` stores little-endian, so every
# colour handed to framebuf (fill, text, blit key) is the BYTE-SWAPPED value. Files hold big-endian
# pixels and are copied into the framebuffer unchanged. Use rgb() for every colour in game code;
# never write a raw 565 literal.

KEY_RGB = (255, 0, 255)      # transparent colour in John's source art (#FF00FF)
KEY_BE = 0xF81F              # its RGB565 value as stored in a file (big-endian number)
KEY = 0x1FF8                 # the same bytes read by framebuf: the blit key


def rgb565(r, g, b):
    """Plain RGB565 (the number whose high byte goes down the wire first)."""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def swap(v):
    """Swap the two bytes of a 16-bit value."""
    return ((v & 0xFF) << 8) | (v >> 8)


def rgb(r, g, b):
    """Colour for framebuf calls on this panel (byte-swapped RGB565)."""
    return swap(rgb565(r, g, b))
