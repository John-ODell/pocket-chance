"""Convert John's source art (assets/src/**) to .565 files for the board (assets/out/).

Rulings: DR-002 (4-byte header: width, height, 16-bit little-endian; then big-endian RGB565;
extension .565; any non-magenta pixel that would become the transparent value is nudged one shade),
DR-003 (big-endian pixels, no rotation: art is drawn upright), DR-004 (Pillow, Mac side only),
DR-006 (exact sizes from assets/ASSETS.md; wrong sizes are rejected, not stretched).

Usage (from the repo root):
    python3 tools/convert_assets.py                 convert everything under assets/src
    python3 tools/convert_assets.py path/to/x.bmp   convert one or more files
    --resize    nearest-neighbour resize to the expected size instead of rejecting
    --any-size  accept a file at whatever size it is (experiments only)
Output goes flat into assets/out/<name>.565 and is uploaded to /assets on the board.
"""
import os
import re
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from pixfmt import rgb565, KEY_RGB, KEY_BE  # noqa: E402
import sheets  # noqa: E402

# Expected sizes by file name (assets/ASSETS.md). First match wins.
SIZES = (
    (r'^c_[A23456789TJQK][SHDC]$', (40, 56)),
    (r'^c_back$', (40, 56)),
    (r'^chip_\d+$', (24, 24)),
    (r'^table$', (240, 240)),
    (r'^menu_background$', (240, 240)),
    (r'^cabinet$', (240, 240)),
    (r'^logo$', (200, 40)),
    (r'^banner_jackpot$', (200, 40)),
    (r'^icon_\w+$', (48, 48)),
    (r'^banner_\w+$', (160, 32)),
    (r'^sym_\w+$', (56, 56)),
)


def expected_size(name):
    for pat, size in SIZES:
        if re.match(pat, name):
            return size
    return None


def to_565(pixels, w, h):
    """pixels: iterable of (r, g, b) in row order. Returns the complete file contents (bytes)."""
    out = bytearray(4 + w * h * 2)
    struct.pack_into('<HH', out, 0, w, h)
    i = 4
    nudged = 0
    for r, g, b in pixels:
        if (r, g, b) == KEY_RGB:
            v = KEY_BE
        else:
            v = rgb565(r, g, b)
            if v == KEY_BE:            # a real pixel that happens to match the key
                v = rgb565(r, g, max(0, b - 8))
                nudged += 1
        out[i] = v >> 8
        out[i + 1] = v & 0xFF
        i += 2
    return bytes(out), nudged


# Text zones on the blackjack table (games/blackjack.py bands), as (x, y, w, h). Text is gold, white
# or grey, so the art under these boxes must be dark and calm. See assets/ASSETS.md "Readability".
TABLE_ZONES = (
    ('top line (chips and bet)', (0, 0, 240, 24)),
    ('dealer total', (0, 84, 100, 12)),
    ('player totals', (0, 156, 240, 12)),
    ('banner and prompts', (16, 168, 208, 72)),
)
# Text zones on the main menu (pocket.py). Text sits on dark plates there, so these are advisory.
MENU_ZONES = (
    ('title and balance', (16, 8, 208, 52)),
    ('menu row 1', (16, 70, 208, 48)),
    ('menu row 2', (16, 118, 208, 48)),
    ('menu row 3', (16, 166, 208, 48)),
    ('footer', (16, 222, 208, 16)),
)
# Text zones on the slots cabinet (DR-023). The three reel windows (x 18/92/166, y 92-147) are
# covered by symbols and are not checked.
CABINET_ZONES = (
    ('top line (chips and bet)', (0, 0, 240, 24)),
    ('win line', (20, 156, 200, 12)),
    ('banner and prompts', (16, 168, 208, 72)),
)
SYMBOL_NAMES = ('cherry', 'lemon', 'orange', 'bell', 'bar', 'seven', 'diamond', 'star')
MAX_MEAN_LUMA = 100        # 0..255; the text colours are 160..255
MAX_BRIGHT_SHARE = 0.25    # share of pixels brighter than 128 behind the text


def luma(r, g, b):
    return (299 * r + 587 * g + 114 * b) // 1000


def zone_warnings(pixels, w, h, zones=TABLE_ZONES):
    """pixels: list of (r, g, b) in row order. Returns a list of plain-language warnings."""
    out = []
    for name, (zx, zy, zw, zh) in zones:
        total = 0
        bright = 0
        n = 0
        for y in range(zy, min(zy + zh, h)):
            row = y * w
            for x in range(zx, min(zx + zw, w)):
                r, g, b = pixels[row + x]
                l = luma(r, g, b)
                total += l
                if l > 128:
                    bright += 1
                n += 1
        if not n:
            continue
        mean = total // n
        share = bright / float(n)
        if mean > MAX_MEAN_LUMA:
            out.append('%s: too light (average brightness %d of 255, keep it under %d) so gold and white text will be hard to read'
                       % (name, mean, MAX_MEAN_LUMA))
        elif share > MAX_BRIGHT_SHARE:
            out.append('%s: %d%% of the pixels are bright; keep this area calm and dark' % (name, int(share * 100)))
    return out


def convert_file(src, out_dir, resize=False, any_size=False):
    from PIL import Image
    name = os.path.splitext(os.path.basename(src))[0]
    if name != name.lower() or ' ' in name:
        name_l = name.lower().replace(' ', '')
        print('  note: %s renamed to %s (names are lowercase, no spaces)' % (name, name_l))
        name = name_l
    # card names keep the capital rank/suit: c_AS, not c_as. Restore them.
    m = re.match(r'^c_([a23456789tjqk])([shdc])$', name)
    if m:
        name = 'c_' + m.group(1).upper() + m.group(2).upper()
    img = Image.open(src).convert('RGB')
    want = expected_size(name)
    if want is None and not any_size:
        raise ValueError('%s: unknown asset name, no size rule in ASSETS.md' % name)
    if want is not None and img.size != want:
        if resize:
            img = img.resize(want, Image.NEAREST)
        elif not any_size:
            raise ValueError('%s: is %dx%d, must be %dx%d' % (name, img.size[0], img.size[1], want[0], want[1]))
    w, h = img.size
    get = getattr(img, 'get_flattened_data', None) or img.getdata   # Pillow 12.3 renamed it
    pixels = list(get())
    data, nudged = to_565(pixels, w, h)
    zones = {'table': TABLE_ZONES, 'menu_background': MENU_ZONES, 'cabinet': CABINET_ZONES}.get(name)
    if zones:
        for warning in zone_warnings(pixels, w, h, zones):
            print('  WARNING %s: %s' % (name, warning))
    if name.startswith('sym_') and name[4:] not in SYMBOL_NAMES:
        print('  WARNING %s: not one of the eight slot symbols (%s); the game will not use it'
              % (name, ', '.join(SYMBOL_NAMES)))
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, name + '.565')
    with open(dst, 'wb') as f:
        f.write(data)
    note = ' (%d pixel%s nudged off the transparent colour)' % (nudged, '' if nudged == 1 else 's') if nudged else ''
    print('  %s -> %s  %dx%d  %d bytes%s' % (os.path.relpath(src), os.path.relpath(dst), w, h, len(data), note))
    return dst


def find_source(src_root, name):
    """Path of name.bmp/.png anywhere under assets/src (case-insensitive stem), or None."""
    for d, _, files in os.walk(src_root):
        for n in files:
            stem, ext = os.path.splitext(n)
            if ext.lower() in ('.bmp', '.png') and stem.lower().replace(' ', '') == name.lower():
                return os.path.join(d, n)
    return None


def pack_sheet(sheet, src_root, out_dir, resize=False):
    """Write assets/out/<sheet>.565 from the members' source files (DR-024). Missing members become
    magenta (transparent) placeholders. Returns (path, missing names) or (None, missing) when no
    member exists at all."""
    from PIL import Image
    w, h, names = sheets.SHEETS[sheet]
    pixels = []
    missing = []
    found = 0
    for name in names:
        src = find_source(src_root, name)
        if src is None:
            missing.append(name)
            pixels.extend([KEY_RGB] * (w * h))
            continue
        img = Image.open(src).convert('RGB')
        if img.size != (w, h):
            if resize:
                img = img.resize((w, h), Image.NEAREST)
            else:
                raise ValueError('%s: is %dx%d, must be %dx%d' % (name, img.size[0], img.size[1], w, h))
        get = getattr(img, 'get_flattened_data', None) or img.getdata
        pixels.extend(list(get()))
        found += 1
    if not found:
        return None, missing
    data, nudged = to_565(pixels, w, h * len(names))
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, sheet + '.565')
    with open(dst, 'wb') as f:
        f.write(data)
    note = ' (%d pixel%s nudged)' % (nudged, '' if nudged == 1 else 's') if nudged else ''
    print('  sheet %s -> %s  %d of %d members, %d bytes%s' % (sheet, os.path.relpath(dst), found, len(names), len(data), note))
    if missing:
        print('    missing (magenta placeholders): ' + ', '.join(missing))
    return dst, missing


def main(argv):
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    resize = '--resize' in argv
    any_size = '--any-size' in argv
    files = [a for a in argv if not a.startswith('--')]
    if not files:
        src_root = os.path.join(root, 'assets', 'src')
        for d, _, names in os.walk(src_root):
            for n in sorted(names):
                if n.lower().endswith(('.bmp', '.png')):
                    files.append(os.path.join(d, n))
    out_dir = os.path.join(root, 'assets', 'out')
    src_root = os.path.join(root, 'assets', 'src')
    errors = 0
    singles = 0
    for f in files:
        stem = os.path.splitext(os.path.basename(f))[0].lower().replace(' ', '')
        m = re.match(r'^c_([a23456789tjqk])([shdc])$', stem)
        if m:
            stem = 'c_' + m.group(1).upper() + m.group(2).upper()
        if sheets.member(stem) is not None:
            continue                       # packed into its sheet below
        try:
            convert_file(f, out_dir, resize, any_size)
            singles += 1
        except Exception as e:  # report every file, then fail
            print('  ERROR %s: %s' % (os.path.relpath(f), e))
            errors += 1
    packed = 0
    for sheet in sorted(sheets.SHEETS):
        try:
            dst, missing = pack_sheet(sheet, src_root, out_dir, resize)
            if dst:
                packed += 1
        except Exception as e:
            print('  ERROR sheet %s: %s' % (sheet, e))
            errors += 1
    if not singles and not packed and not errors:
        print('nothing to convert: put BMP or PNG files under assets/src/')
    print('%d single file(s), %d sheet(s), %d error(s)' % (singles, packed, errors))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
