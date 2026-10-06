# Pocket Chance entry point. Installs on the board as /pocket.py (ruling DR-001); renaming it to
# main.py so it runs at boot is a separate step John approves in UPLOAD.md.
# Start-up order matters (HR-001, HR-015): clock fix, then the framebuffer before anything else
# large, then the rest. A game module is imported when chosen and dropped on exit to free RAM.

FAST_SPI = True          # DR-050: peripheral clock from the 125 MHz system PLL (62.5 MHz SPI).
                         # False = the firmware's 48 MHz source (24 MHz SPI, 46 ms a frame), else identical.
SPI_BAUD = 62_500_000    # honest with DR-050: the repr says what it gets. Fallback 31_250_000.
SAVE_PATH = '/save.json'
CAR_SEATS = 4            # other players at the Caribbean table, 0 to 4 (DR-069)
UTH_SEATS = 4            # other players at the Ultimate table, 0 to 4 (DR-044)
UTH_HINT = True          # river dealer-outs count on the Ultimate prompt (DR-042 addendum)
BAC_SEATS = 5            # other players at the baccarat table, 0 to 5 (DR-055)

import sys
import gc

if '/games' not in sys.path:
    sys.path.append('/games')

import machine
import utime
# DR-050 / HR-F05: the supported way to source clk_peri from the system PLL on v1.29.0; same frame
# time as the old register poke, and MicroPython's cached clock follows, so SPI speeds are honest.
# Must run before the SPI object is created. A power cycle resets it, so it is a boot-time call.
machine.freq(125_000_000, 125_000_000 if FAST_SPI else 48_000_000)

from lcd import LCD
lcd = LCD(SPI_BAUD)
_t = utime.ticks_us()
lcd.show()
print('RESULT first show us=%d spi=%s' % (utime.ticks_diff(utime.ticks_us(), _t), lcd.spi))
gc.collect()

import random
import font
from pixfmt import rgb
from buttons import Buttons
from art import Assets
from save import Store
from bankroll import Bankroll

BG = rgb(10, 20, 30)
WHITE = rgb(255, 255, 255)
GOLD = rgb(240, 200, 60)
GREY = rgb(140, 140, 140)

# (label, module or None for "soon" or 'off', icon). Labels must fit the label area at size 2:
# 9 characters at most (tests/test_screens.py checks). Full game names are used inside the games.
MENU = (('Blackjack', 'blackjack', 'icon_blackjack'),
        ('Ultimate', 'holdem', 'icon_holdem'),       # DR-061: Ultimate Texas Hold'em
        ('Caribbean', 'caribbean', 'icon_stud'),     # DR-062: the flop game John described; Stud is archived
        ('Baccarat', 'baccarat', 'icon_baccarat'),   # DR-057; John asked to test it on the board
        ('Off', 'off', None))                        # slots was dropped (D-009)
VISIBLE = 3                                  # rows on screen (DR-022: scrolling list)


class Ctx:
    pass


def message(text, ms=2000):
    lcd.fill(BG)
    y = 100
    for line in text.split('\n'):
        font.text_centred(lcd, line, 120, y, WHITE, 1)
        y += 12
    lcd.show()
    utime.sleep_ms(ms)


# Menu geometry. Rows are 48 px (an icon is 48x48). The icon sits at the left of the row box and the
# label (size-2 text, 16 px) is centred in the rest of the box, so the highlight always surrounds its
# own word (John saw the old box sitting far to the right of the word). Checked by tests/test_screens.py.
# Background (D-007): /assets/menu_background.565, John's photo, read whole on menu entry and by
# row bands on a selection change (DR-005). Text sits on small dark plates so it reads over the photo.
ROW_Y = (70, 118, 166)
ROW_X, ROW_W, ROW_H = 16, 208, 48
ICON_W = 56                                  # icon slot at the left of the box
LABEL_X0 = ROW_X + ICON_W                    # label area: LABEL_X0 .. ROW_X + ROW_W
TITLE_Y, BALANCE_Y, FOOTER_Y = 14, 40, 226
PANEL = rgb(30, 50, 80)                      # selected row (photo menu, D-007)
PLATE = rgb(8, 10, 18)                       # under text on unselected rows, title, footer (photo menu)
BACKGROUND = 'menu_background'
# Style A (ruling DR-072, "casino felt and chips"), drawn in code when John's photo is not on the
# board: a felt shaded top to bottom in 4-row strips, a double gold border, the title with a drop
# shadow, the chips on a cream plaque, one pill per row in that game's felt colour (DR-065) with a
# gold outline on the chosen one, a gold chip in the right margin as the cursor, and a code-drawn
# suit sign in the icon slot until the icon art exists. No buffers: every band is redrawn from
# its row index (menu_background), so RAM is unchanged.
SHADES = tuple(rgb(0, 70 + (30 * i) // 59, 30 + (15 * i) // 59) for i in range(60))
CREAM = rgb(240, 232, 200)
BLACK = rgb(0, 0, 0)
BORDER = (4, 7)                              # the two gold border lines, px in from each edge
PILL_R = 23
GAME_COLOUR = {'blackjack': (rgb(0, 95, 42), rgb(0, 60, 26)),      # (selected, unselected) pill colours
               'holdem': (rgb(20, 40, 110), rgb(12, 25, 70)),
               'caribbean': (rgb(110, 20, 30), rgb(70, 12, 18)),
               'baccarat': (rgb(0, 80, 80), rgb(0, 50, 50)),          # DR-065 teal
               'off': (rgb(70, 70, 70), rgb(45, 45, 45))}
SUIT_RED = rgb(230, 70, 70)


def label_text(i):
    """(label, suffix) for menu row i; the suffix is drawn small."""
    label, mod, icon = MENU[i]
    return label, ('soon' if mod is None else '')


def label_width(i):
    return font.width(label_text(i)[0], 2)      # the small "soon" tag sits under the label


def label_x(i):
    """Left edge that centres row i's label (plus its small suffix) in the label area."""
    return LABEL_X0 + (ROW_X + ROW_W - LABEL_X0 - label_width(i)) // 2


def label_box(i, slot):
    """Dark plate under item i's label drawn in row `slot` (photo menu): (x, y, w, h), inside the row box."""
    h = 34 if label_text(i)[1] else 24          # taller when the "soon" tag is under the label
    return label_x(i) - 4, ROW_Y[slot] + 12, label_width(i) + 8, h


def top_for(sel, top):
    """First visible item so that `sel` is on screen, moving the window as little as possible."""
    if sel < top:
        return sel
    if sel >= top + VISIBLE:
        return sel - VISIBLE + 1
    return top


def has_menu_art(ctx):
    if not hasattr(ctx, 'menu_art'):
        ctx.menu_art = ctx.assets.size(BACKGROUND) is not None
    return ctx.menu_art


def felt_rows(y, h):
    """Style A background for rows y..y+h-1: the shade strips and the border lines that cross them."""
    yy = y - y % 4
    while yy < y + h:
        top = yy if yy > y else y
        bottom = yy + 4 if yy + 4 < y + h else y + h
        lcd.fill_rect(0, top, 240, bottom - top, SHADES[yy // 4])
        yy += 4
    for b in BORDER:
        lcd.vline(b, y, h, GOLD)
        lcd.vline(239 - b, y, h, GOLD)
        for hy in (b, 239 - b):
            if y <= hy < y + h:
                lcd.hline(b, hy, 240 - 2 * b, GOLD)


def menu_background(ctx, y, h):
    """Restore rows y..y+h-1 of the menu background: John's photo from flash, or the style-A felt."""
    if has_menu_art(ctx) and ctx.assets.background_rows(lcd, BACKGROUND, y, h):
        return
    felt_rows(y, h)


def plate_text(s, y, size, col):
    """Centred text on a dark plate with a 6 px border (photo menu)."""
    w = font.width(s, size)
    x = 120 - w // 2
    lcd.fill_rect(x - 6, y - 3, w + 12, font.CH * size + 6, PLATE)
    font.text(lcd, s, x, y, col, size)


def plaque_text(s, y, size, col):
    """Centred text on a cream plaque with rounded ends (style A)."""
    w = font.width(s, size)
    h = font.CH * size + 6
    x = 120 - w // 2
    r = h // 2
    lcd.fill_rect(x - 2, y - 3, w + 4, h, CREAM)
    lcd.ellipse(x - 2, y - 3 + r, r, r, CREAM, True)
    lcd.ellipse(x + w + 1, y - 3 + r, r, r, CREAM, True)
    font.text(lcd, s, x, y, col, size)


def shadow_text(s, x, y, col, size):
    """Text with a 2 px drop shadow below it."""
    font.text(lcd, s, x, y + 2, BLACK, size)
    font.text(lcd, s, x, y, col, size)


def pill(x, y, w, h, col, outline=None):
    """A row-wide pill: a rectangle with half-disc ends; optional 1 px outline."""
    r = h // 2
    lcd.fill_rect(x + r, y, w - 2 * r, h, col)
    lcd.ellipse(x + r, y + r, r, r, col, True)
    lcd.ellipse(x + w - r - 1, y + r, r, r, col, True)
    if outline is not None:
        lcd.hline(x + r, y, w - 2 * r, outline)
        lcd.hline(x + r, y + h - 1, w - 2 * r, outline)
        lcd.ellipse(x + r, y + r, r, r, outline, False, 0x6)             # left half: quadrants 2 and 3
        lcd.ellipse(x + w - r - 1, y + r, r, r, outline, False, 0x9)     # right half: quadrants 1 and 4


def suit_sign(mod, cx, cy):
    """Code-drawn stand-in for a menu icon: spade (Blackjack), diamond (Ultimate), club (Caribbean),
    heart (Baccarat), power sign (Off), about 32 px tall, centred on (cx, cy)."""
    if mod == 'blackjack':
        for i in range(14):                                   # the spade's point: a triangle of hlines
            lcd.hline(cx - i, cy - 15 + i, 2 * i + 1, CREAM)
        lcd.ellipse(cx - 6, cy + 1, 7, 7, CREAM, True)
        lcd.ellipse(cx + 6, cy + 1, 7, 7, CREAM, True)
        lcd.fill_rect(cx - 2, cy + 4, 4, 10, CREAM)
        lcd.fill_rect(cx - 7, cy + 13, 14, 2, CREAM)
    elif mod == 'holdem':
        for i in range(16):                                   # a diamond: two triangles of hlines
            w = (12 * i) // 15
            lcd.hline(cx - w, cy - 15 + i, 2 * w + 1, SUIT_RED)
            lcd.hline(cx - w, cy + 15 - i, 2 * w + 1, SUIT_RED)
    elif mod == 'caribbean':
        lcd.ellipse(cx, cy - 7, 7, 7, CREAM, True)
        lcd.ellipse(cx - 8, cy + 3, 7, 7, CREAM, True)
        lcd.ellipse(cx + 8, cy + 3, 7, 7, CREAM, True)
        lcd.fill_rect(cx - 2, cy + 2, 4, 12, CREAM)
        lcd.fill_rect(cx - 7, cy + 13, 14, 2, CREAM)
    elif mod == 'baccarat':
        lcd.ellipse(cx - 6, cy - 6, 7, 7, SUIT_RED, True)      # a heart: two lobes and a point
        lcd.ellipse(cx + 6, cy - 6, 7, 7, SUIT_RED, True)
        for i in range(15):
            w = 13 - (13 * i) // 14
            lcd.hline(cx - w, cy - 3 + i, 2 * w + 1, SUIT_RED)
    else:
        lcd.ellipse(cx, cy, 12, 12, CREAM, False)
        lcd.ellipse(cx, cy, 11, 11, CREAM, False)
        lcd.fill_rect(cx - 4, cy - 15, 8, 6, SHADES[cy // 4])  # a gap at the top of the ring
        lcd.fill_rect(cx - 2, cy - 15, 4, 14, CREAM)


def draw_row(ctx, slot, top, sel):
    """Draw menu item top+slot in screen row `slot`, plus the scroll arrow on the edge rows."""
    i = top + slot
    y = ROW_Y[slot]
    label, mod, icon = MENU[i]
    photo = has_menu_art(ctx)
    if photo:
        col = GOLD if i == sel else (GREY if mod is None else WHITE)
        if i == sel:
            lcd.fill_rect(ROW_X, y, ROW_W, ROW_H, PANEL)
            lcd.rect(ROW_X, y, ROW_W, ROW_H, GOLD)
        else:
            px, py, pw, ph = label_box(i, slot)
            lcd.fill_rect(px, py, pw, ph, PLATE)
    else:
        on, off_col = GAME_COLOUR.get(mod, GAME_COLOUR['off'])
        if i == sel:
            pill(ROW_X, y, ROW_W, ROW_H, on, GOLD)
            lcd.ellipse(ROW_X + ROW_W + 4, y + ROW_H // 2, 3, 3, GOLD, True)       # the chip cursor,
            lcd.pixel(ROW_X + ROW_W + 4, y + ROW_H // 2, WHITE)                    # clear of the border lines
            col = CREAM
        else:
            pill(ROW_X, y, ROW_W, ROW_H, off_col)
            col = GREY if mod is None else WHITE
    if not (icon and ctx.assets.blit(lcd, icon, ROW_X + 4, y)):
        if photo:
            lcd.rect(ROW_X + 12, y + 8, 32, 32, col)       # placeholder until icon art exists
        else:
            suit_sign(mod, ROW_X + 28, y + ROW_H // 2)
    lx = label_x(i)
    font.text(lcd, label, lx, y + 16, col, 2)           # no shadow on labels: size-2 text is the cost (HR-072)
    if mod is None:
        font.text(lcd, 'soon', lx + (label_width(i) - font.width('soon', 1)) // 2, y + 35, GREY, 1)
    # gold arrows in the right margin when the list continues (DR-022)
    if slot == 0 and top > 0:
        font.text(lcd, '^', ROW_X + ROW_W + 4, y + 2, GOLD, 1)
    if slot == VISIBLE - 1 and top + VISIBLE < len(MENU):
        font.text(lcd, 'v', ROW_X + ROW_W + 4, y + ROW_H - 10, GOLD, 1)


def draw_menu(ctx, sel, top=0):
    """Menu entry: one full background read (or the felt), everything drawn, one show() (DR-005)."""
    photo = has_menu_art(ctx) and ctx.assets.background(lcd, BACKGROUND)
    if not photo:
        felt_rows(0, 240)
        for yy in range(10, 62, 8):                           # a faint diamond pattern on the title band
            for xx in range(12 + (yy // 8 % 2) * 4, 228, 8):
                lcd.pixel(xx, yy, CREAM)
    if ctx.assets.blit(lcd, 'logo', 20, 6):
        (plate_text if photo else plaque_text)('$%d' % ctx.bankroll.balance, 52, 1, WHITE if photo else BLACK)
    elif photo:
        plate_text('Pocket Chance', TITLE_Y, 2, GOLD)
        plate_text('$%d' % ctx.bankroll.balance, BALANCE_Y, 2, WHITE)
    else:
        shadow_text('Pocket Chance', 120 - font.width('Pocket Chance', 2) // 2, TITLE_Y, GOLD, 2)
        plaque_text('$%d' % ctx.bankroll.balance, BALANCE_Y, 2, BLACK)
    for slot in range(VISIBLE):
        draw_row(ctx, slot, top, sel)
    if photo:
        plate_text('joystick: move   A: pick', FOOTER_Y, 1, GREY)
    else:
        font.text_centred(lcd, 'joystick: move   A: pick', 120, FOOTER_Y, CREAM, 1)
    lcd.show()


def menu_select(ctx, old, new, top):
    """Selection change. If `new` is on screen, restore and redraw only the two rows that changed
    and push their bands; otherwise scroll: redraw all visible rows as one band. Returns the new top."""
    new_top = top_for(new, top)
    if new_top == top:
        for i in (old, new):
            slot = i - top
            menu_background(ctx, ROW_Y[slot], ROW_H)
            draw_row(ctx, slot, top, new)
            lcd.show_band(ROW_Y[slot], ROW_H)
    else:
        menu_background(ctx, ROW_Y[0], ROW_H * VISIBLE)
        for slot in range(VISIBLE):
            draw_row(ctx, slot, new_top, new)
        lcd.show_band(ROW_Y[0], ROW_H * VISIBLE)
    return new_top


def play(ctx, modname):
    ctx.assets.release_sheets()                       # the game opens its own sheets
    gc.collect()
    before = gc.mem_free()
    mod = __import__(modname)
    gc.collect()                                      # drop the compile garbage before the game starts
    print('RESULT import %s mem_free before=%d after=%d' % (modname, before, gc.mem_free()))
    try:
        mod.run(ctx)
    finally:
        del mod
        if modname in sys.modules:
            del sys.modules[modname]
        ctx.assets.release_sheets()
        gc.collect()
        print('RESULT after %s mem_free=%d' % (modname, gc.mem_free()))
        ctx.assets.use_sheets(('icons',))


def off():
    lcd.fill(0)
    lcd.show()
    lcd.backlight(0)
    while True:
        utime.sleep_ms(1000)


def main():
    ctx = Ctx()
    ctx.lcd = lcd
    ctx.buttons = Buttons()
    ctx.assets = Assets('/assets')
    ctx.store = Store(SAVE_PATH)
    ctx.car_seats = CAR_SEATS
    ctx.uth_seats = UTH_SEATS
    ctx.uth_hint = UTH_HINT
    ctx.bac_seats = BAC_SEATS
    try:
        random.seed()           # hardware RNG on rp2
    except Exception:
        random.seed(utime.ticks_us())
    ctx.rng = random
    bank, msg = ctx.store.load()
    ctx.assets.use_sheets(('icons',))                 # DR-024: the menu's icon sheet stays open
    ctx.bankroll = Bankroll(bank) if bank is not None else Bankroll()
    gc.collect()
    print('RESULT boot mem_free=%d fast_spi=%s freq=%s' % (gc.mem_free(), FAST_SPI, machine.freq()))
    if msg:
        message(msg)
    sel = 0
    top = 0
    draw_menu(ctx, sel, top)
    while True:
        for key in ctx.buttons.poll():
            if key == 'UP' and sel > 0:
                sel -= 1
                top = menu_select(ctx, sel + 1, sel, top)
            elif key == 'DOWN' and sel < len(MENU) - 1:
                sel += 1
                top = menu_select(ctx, sel - 1, sel, top)
            elif key in ('A', 'PRESS'):
                mod = MENU[sel][1]
                if mod == 'off':
                    off()
                elif mod:
                    play(ctx, mod)
                    draw_menu(ctx, sel, top)
        utime.sleep_ms(15)


main()
