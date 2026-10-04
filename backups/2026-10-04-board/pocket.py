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


def draw_menu(ctx, sel):
    lcd.fill(BG)
    if not ctx.assets.blit(lcd, 'logo', 20, 12):
        font.text_centred(lcd, 'Pocket Chance', 120, 20, GOLD, 2)
    font.text_centred(lcd, '$%d' % ctx.bankroll.balance, 120, 52, WHITE, 1)
    y = 80
    for i, (label, mod, icon) in enumerate(MENU):
        col = GOLD if i == sel else (GREY if mod is None else WHITE)
        if i == sel:
            lcd.rect(28, y - 6, 184, 44, GOLD)
        if icon and ctx.assets.blit(lcd, icon, 36, y - 8):
            pass
        font.text(lcd, label + ('' if mod or mod == 'off' else ' (soon)'), 92, y + 8, col, 2)
        y += 52
    font.text_centred(lcd, 'joystick: move   A: pick', 120, 226, GREY, 1)
    lcd.show()


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
                draw_menu(ctx, sel)
            elif key == 'DOWN' and sel < len(MENU) - 1:
                sel += 1
                draw_menu(ctx, sel)
            elif key in ('A', 'PRESS'):
                mod = MENU[sel][1]
                if mod == 'off':
                    off()
                elif mod:
                    play(ctx, mod)
                    draw_menu(ctx, sel)
        utime.sleep_ms(15)


main()
