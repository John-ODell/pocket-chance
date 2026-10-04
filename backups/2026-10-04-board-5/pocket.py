# Pocket Chance entry point. Installs on the board as /pocket.py (ruling DR-001); renaming it to
# main.py so it runs at boot is a separate step John approves in UPLOAD.md.
# Start-up order matters (HR-001, HR-015): clock fix, then the framebuffer before anything else
# large, then the rest. A game module is imported when chosen and dropped on exit to free RAM.

FAST_SPI = True          # DR-015 off switch. False = screen link at 24 MHz, everything else the same.
SPI_BAUD = 62_500_000    # real 62.5 MHz with the fix on; use 12_000_000 for a real 31.25 MHz (HR-015)
SAVE_PATH = '/save.json'

import sys
import gc

if '/games' not in sys.path:
    sys.path.append('/games')

if FAST_SPI:
    from clocks import fast_peripherals
    fast_peripherals()

from lcd import LCD
lcd = LCD(SPI_BAUD)
gc.collect()

import utime
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

MENU = (('Blackjack', 'blackjack', 'icon_blackjack'),
        ('Slots', None, 'icon_slots'),
        ('Off', 'off', None))


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
PANEL = rgb(30, 50, 80)                      # selected row
PLATE = rgb(8, 10, 18)                       # under text on unselected rows, title, footer
BACKGROUND = 'menu_background'


def label_text(i):
    """(label, suffix) for menu row i; the suffix is drawn small."""
    label, mod, icon = MENU[i]
    return label, ('soon' if mod is None else '')


def label_width(i):
    label, suffix = label_text(i)
    return font.width(label, 2) + (8 + font.width(suffix, 1) if suffix else 0)


def label_x(i):
    """Left edge that centres row i's label (plus its small suffix) in the label area."""
    return LABEL_X0 + (ROW_X + ROW_W - LABEL_X0 - label_width(i)) // 2


def label_box(i):
    """Dark plate under row i's label: (x, y, w, h), inside the row box."""
    return label_x(i) - 4, ROW_Y[i] + 12, label_width(i) + 8, 24


def has_menu_art(ctx):
    if not hasattr(ctx, 'menu_art'):
        ctx.menu_art = ctx.assets.size(BACKGROUND) is not None
    return ctx.menu_art


def menu_background(ctx, y, h):
    """Restore rows y..y+h-1 of the menu background from flash, or plain colour without art."""
    if has_menu_art(ctx) and ctx.assets.background_rows(lcd, BACKGROUND, y, h):
        return
    lcd.fill_rect(0, y, 240, h, BG)


def plate_text(s, y, size, col):
    """Centred text on a dark plate with a 6 px border."""
    w = font.width(s, size)
    x = 120 - w // 2
    lcd.fill_rect(x - 6, y - 3, w + 12, font.CH * size + 6, PLATE)
    font.text(lcd, s, x, y, col, size)


def draw_row(ctx, i, sel):
    y = ROW_Y[i]
    label, mod, icon = MENU[i]
    col = GOLD if i == sel else (GREY if mod is None else WHITE)
    if i == sel:
        lcd.fill_rect(ROW_X, y, ROW_W, ROW_H, PANEL)
        lcd.rect(ROW_X, y, ROW_W, ROW_H, GOLD)
    else:
        px, py, pw, ph = label_box(i)
        lcd.fill_rect(px, py, pw, ph, PLATE)
    if not (icon and ctx.assets.blit(lcd, icon, ROW_X + 4, y)):
        lcd.rect(ROW_X + 12, y + 8, 32, 32, col)       # placeholder until icon art exists
    lx = label_x(i)
    font.text(lcd, label, lx, y + 16, col, 2)
    if mod is None:
        font.text(lcd, 'soon', lx + font.width(label, 2) + 8, y + 20, GREY, 1)


def draw_menu(ctx, sel):
    """Menu entry: one full background read, everything drawn, one show() (DR-005)."""
    if not (has_menu_art(ctx) and ctx.assets.background(lcd, BACKGROUND)):
        lcd.fill(BG)
    if ctx.assets.blit(lcd, 'logo', 20, 6):
        plate_text('$%d' % ctx.bankroll.balance, 52, 1, WHITE)
    else:
        plate_text('Pocket Chance', TITLE_Y, 2, GOLD)
        plate_text('$%d' % ctx.bankroll.balance, BALANCE_Y, 2, WHITE)
    for i in range(len(MENU)):
        draw_row(ctx, i, sel)
    plate_text('joystick: move   A: pick', FOOTER_Y, 1, GREY)
    lcd.show()


def menu_select(ctx, old, new):
    """Selection change: restore and redraw only the two rows that changed, push their bands."""
    for i in (old, new):
        menu_background(ctx, ROW_Y[i], ROW_H)
        draw_row(ctx, i, new)
        lcd.show_band(ROW_Y[i], ROW_H)


def play(ctx, modname):
    gc.collect()
    before = gc.mem_free()
    mod = __import__(modname)
    print('RESULT import %s mem_free before=%d after=%d' % (modname, before, gc.mem_free()))
    try:
        mod.run(ctx)
    finally:
        del mod
        if modname in sys.modules:
            del sys.modules[modname]
        gc.collect()
        print('RESULT after %s mem_free=%d' % (modname, gc.mem_free()))


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
    try:
        random.seed()           # hardware RNG on rp2
    except Exception:
        random.seed(utime.ticks_us())
    ctx.rng = random
    bank, msg = ctx.store.load()
    ctx.bankroll = Bankroll(bank) if bank is not None else Bankroll()
    gc.collect()
    print('RESULT boot mem_free=%d fast_spi=%s' % (gc.mem_free(), FAST_SPI))
    if msg:
        message(msg)
    sel = 0
    draw_menu(ctx, sel)
    while True:
        for key in ctx.buttons.poll():
            if key == 'UP' and sel > 0:
                sel -= 1
                menu_select(ctx, sel + 1, sel)
            elif key == 'DOWN' and sel < len(MENU) - 1:
                sel += 1
                menu_select(ctx, sel - 1, sel)
            elif key in ('A', 'PRESS'):
                mod = MENU[sel][1]
                if mod == 'off':
                    off()
                elif mod:
                    play(ctx, mod)
                    draw_menu(ctx, sel)
        utime.sleep_ms(15)


main()
