"""Headless run of the board code under CPython with fake machine/framebuf/utime modules.

This catches crashes, wrong state flow and asset-loading mistakes before the expert sees the code.
It says nothing about timing, colours on the real panel, or MicroPython-only behaviour.
"""
import os
import random
import shutil
import struct
import sys
import tempfile
import unittest

import tests.context  # noqa: F401
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fakes'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))

import machine  # noqa: E402  (the fake)
from convert_assets import to_565  # noqa: E402
from pixfmt import rgb, KEY, KEY_BE  # noqa: E402
from lcd import LCD  # noqa: E402
from buttons import Buttons, PINS  # noqa: E402
from art import Assets  # noqa: E402
from save import Store  # noqa: E402
from bankroll import Bankroll  # noqa: E402
from cards import card_from_name, Shoe  # noqa: E402
import blackjack  # noqa: E402
from blackjack_table import BETTING, PLAYING, RESULT, BROKE  # noqa: E402
import font  # noqa: E402

GPIO = dict(PINS)


def write_565(path, w, h, colour):
    data, _ = to_565([colour] * (w * h), w, h)
    with open(path, 'wb') as f:
        f.write(data)


def write_sheet(adir, sheet, colours):
    """A sheet whose member i is the solid colour colours[i] (magenta where None)."""
    import sheets as sh
    w, h, count = sh.SHEETS[sheet]
    px = []
    for i in range(count):
        c = colours.get(i) if isinstance(colours, dict) else colours[i]
        px.extend([c or (255, 0, 255)] * (w * h))
    data, _ = to_565(px, w, h * count)
    with open(os.path.join(adir, sheet + '.565'), 'wb') as f:
        f.write(data)


class Ctx:
    pass


def make_ctx(asset_dir, save_dir, balance=1000):
    ctx = Ctx()
    ctx.lcd = LCD()
    ctx.buttons = Buttons()
    ctx.assets = Assets(asset_dir)
    ctx.store = Store(os.path.join(save_dir, 'save.json'))
    ctx.bankroll = Bankroll(balance)
    ctx.rng = random.Random(3)
    return ctx


class Lcd(unittest.TestCase):
    def test_show_and_bands(self):
        lcd = LCD()
        lcd.fill(rgb(0, 0, 0))
        lcd.spi.written = 0
        lcd.show()
        self.assertGreaterEqual(lcd.spi.written, 115200)
        lcd.spi.written = 0
        lcd.show_band(10, 48)
        self.assertGreaterEqual(lcd.spi.written, 240 * 48 * 2)
        lcd.show_band(230, 48)     # clipped at the bottom
        lcd.show_band(-5, 10)      # clipped at the top
        scratch = bytearray(16384)
        lcd.show_rect(10, 10, 40, 56, scratch)
        lcd.show_rect(0, 0, 240, 240, scratch)   # too big: falls back to a band
        lcd.spi.written = 0
        lcd.show_buf(18, 92, 56, 56, bytearray(56 * 56 * 2))
        self.assertGreaterEqual(lcd.spi.written, 56 * 56 * 2)
        self.assertLess(lcd.spi.written, 56 * 56 * 2 + 64)      # only the window plus commands


class Font(unittest.TestCase):
    def test_sizes_draw_without_error(self):
        lcd = LCD()
        for size in (1, 2, 3):
            font.text(lcd, 'Ab1', 0, 0, rgb(255, 255, 255), size)
            font.text_centred(lcd, 'x', 120, 100, 1, size)
            font.text_right(lcd, 'x', 240, 100, 1, size)
        self.assertEqual(font.width('abc', 2), 48)
        self.assertEqual(lcd.pixel(0, 0), rgb(255, 255, 255))


class AssetsTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.lcd = LCD()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_missing_files_return_false(self):
        a = Assets(self.dir)
        self.assertFalse(a.blit(self.lcd, 'c_AS', 0, 0))
        self.assertFalse(a.background(self.lcd, 'table'))
        self.assertIsNone(a.size('nope'))
        self.assertIn('c_AS', a.missing)

    def test_sprite_blit_with_key(self):
        # a 2x1 sprite: red then magenta (transparent)
        data, _ = to_565([(255, 0, 0), (255, 0, 255)], 2, 1)
        with open(os.path.join(self.dir, 's.565'), 'wb') as f:
            f.write(data)
        a = Assets(self.dir)
        self.lcd.fill(rgb(0, 0, 255))
        self.assertTrue(a.blit(self.lcd, 's', 10, 10))
        self.assertEqual(self.lcd.pixel(10, 10), rgb(255, 0, 0))
        self.assertEqual(self.lcd.pixel(11, 10), rgb(0, 0, 255))   # key skipped
        self.assertEqual(a.size('s'), (2, 1))

    def test_background_and_rows(self):
        write_565(os.path.join(self.dir, 'table.565'), 240, 240, (0, 90, 40))
        a = Assets(self.dir)
        self.assertTrue(a.background(self.lcd, 'table'))
        self.assertEqual(self.lcd.pixel(5, 5), rgb(0, 90, 40))
        self.lcd.fill(0)
        self.assertTrue(a.background_rows(self.lcd, 'table', 100, 20))
        self.assertEqual(self.lcd.pixel(0, 100), rgb(0, 90, 40))
        self.assertEqual(self.lcd.pixel(0, 99), 0)
        self.assertEqual(self.lcd.pixel(0, 120), 0)
        self.assertFalse(a.background_rows(self.lcd, 'table', 230, 20))

    def test_bad_header_or_length_rejected(self):
        p = os.path.join(self.dir, 'bad.565')
        with open(p, 'wb') as f:
            f.write(struct.pack('<HH', 40, 56) + b'\x00' * 10)
        a = Assets(self.dir)
        self.assertFalse(a.blit(self.lcd, 'bad', 0, 0))
        with open(os.path.join(self.dir, 'big.565'), 'wb') as f:
            f.write(struct.pack('<HH', 200, 100) + b'\x00' * (200 * 100 * 2))
        self.assertFalse(a.blit(self.lcd, 'big', 0, 0))   # larger than the scratch

    def test_size_check_is_cached_after_first_open(self):
        import art as art_module
        write_565(os.path.join(self.dir, 'c_AS.565'), 40, 56, (240, 232, 200))
        a = Assets(self.dir)
        calls = []
        real_stat = art_module.os.stat
        art_module.os.stat = lambda p: (calls.append(p), real_stat(p))[1]
        try:
            self.assertTrue(a.blit(self.lcd, 'c_AS', 0, 0))
            self.assertTrue(a.blit(self.lcd, 'c_AS', 0, 0))
            self.assertTrue(a.blit(self.lcd, 'c_AS', 0, 0))
            self.assertEqual(len(calls), 1)                    # stat once, then straight to the pixels
            self.assertEqual(a.known['c_AS'], (40, 56))
            # the pixels are right on a cached open (header skipped, not read as pixels)
            self.assertEqual(self.lcd.pixel(0, 0), rgb(240, 232, 200))
            os.remove(os.path.join(self.dir, 'c_AS.565'))
            self.assertFalse(a.blit(self.lcd, 'c_AS', 0, 0))   # vanished file: graceful
            self.assertIn('c_AS', a.missing)
        finally:
            art_module.os.stat = real_stat

    def test_load_into_ram_buffer(self):
        write_565(os.path.join(self.dir, 'sym_star.565'), 56, 56, (250, 220, 40))
        a = Assets(self.dir)
        buf = bytearray(56 * 56 * 2)
        self.assertEqual(a.load('sym_star', buf), (56, 56))
        self.assertEqual(a.load('sym_star', buf), (56, 56))    # cached path
        import framebuf
        fb = framebuf.FrameBuffer(buf, 56, 56, framebuf.RGB565)
        self.assertEqual(fb.pixel(10, 10), rgb(250, 220, 40))
        self.assertIsNone(a.load('sym_star', bytearray(10)))    # too small
        self.assertIsNone(a.load('nope', buf))

    def test_sheet_blit_load_rows_and_fallbacks(self):
        write_sheet(self.dir, 'cards', {0: (200, 10, 10), 52: (10, 10, 200)})     # AS and the back, rest magenta
        a = Assets(self.dir)
        s = a.sheet('cards')
        self.assertIsNotNone(s)
        self.assertEqual((s.w, s.h, s.count), (40, 56, 53))
        self.assertTrue(s.present(0))
        self.assertFalse(s.present(5))
        self.assertTrue(s.present(52))
        self.lcd.fill(rgb(0, 90, 40))
        self.assertTrue(s.blit(self.lcd, 0, 10, 10))
        self.assertEqual(self.lcd.pixel(15, 15), rgb(200, 10, 10))
        self.assertFalse(s.blit(self.lcd, 5, 100, 10))                # a placeholder: not drawn, caller falls back
        self.assertEqual(self.lcd.pixel(105, 15), rgb(0, 90, 40))
        buf = bytearray(4480)
        self.assertTrue(s.read(52, buf))
        self.assertEqual(buf[0], 0x08)                                  # (10,10,200) -> 0x0859 big-endian, high byte first
        rows = bytearray(80 * 3)
        self.assertTrue(s.rows(0, 10, 3, rows))
        self.assertEqual(rows[0], 0xC8 & 0xF8 | 0x00)                 # red high byte of (200,10,10)
        s.close()
        # through Assets: use_sheets makes blit()/load() read members from the open sheet
        a.use_sheets(('cards', 'chips'))                               # chips sheet absent: ignored
        self.assertIn('cards', a.open_sheets)
        self.assertNotIn('chips', a.open_sheets)
        self.lcd.fill(0)
        self.assertTrue(a.blit(self.lcd, 'c_AS', 0, 0))
        self.assertEqual(self.lcd.pixel(5, 5), rgb(200, 10, 10))
        self.assertFalse(a.blit(self.lcd, 'c_7C', 50, 0))              # placeholder member: False, code-drawn card follows
        self.assertIsNone(a.load('c_7C', buf))
        self.assertEqual(a.load('c_back', buf), (40, 56))
        self.assertIsNone(a.load('c_back', bytearray(10)))
        a.release_sheets()
        self.assertEqual(a.open_sheets, {})
        self.assertFalse(a.blit(self.lcd, 'c_AS', 0, 0))                # no sheet open, no single file: False

    def test_bad_sheet_rejected(self):
        write_565(os.path.join(self.dir, 'cards.565'), 40, 56 * 52, (1, 2, 3))   # one member short
        a = Assets(self.dir)
        self.assertIsNone(a.sheet('cards'))
        self.assertIsNone(a.sheet('not_a_sheet'))
        write_565(os.path.join(self.dir, 'icons.565'), 48, 48 * 4, (1, 2, 3))
        self.assertIsNotNone(a.sheet('icons'))

    def test_wrong_size_background_rejected(self):
        write_565(os.path.join(self.dir, 'table.565'), 120, 120, (0, 90, 40))
        a = Assets(self.dir)
        self.assertFalse(a.background(self.lcd, 'table'))


class ButtonsTests(unittest.TestCase):
    def test_edge_detect(self):
        b = Buttons()
        self.assertEqual(b.poll(), [])
        machine.Pin.registry[GPIO['A']].value(0)
        self.assertEqual(b.poll(), ['A'])
        self.assertEqual(b.poll(), [])          # held: no repeat
        self.assertTrue(b.held('A'))
        machine.Pin.registry[GPIO['A']].value(1)
        self.assertEqual(b.poll(), [])
        machine.Pin.registry[GPIO['A']].value(0)
        self.assertEqual(b.poll(), ['A'])
        machine.Pin.registry[GPIO['A']].value(1)


class BlackjackScreen(unittest.TestCase):
    def setUp(self):
        self.adir = tempfile.mkdtemp()
        self.sdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.adir)
        shutil.rmtree(self.sdir)

    def stack(self, screen, names):
        screen.table.shoe = Shoe(6, random.Random(0), stacked=[card_from_name(n) for n in names])

    def test_full_hand_without_art(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = blackjack.Screen(ctx)
        s.draw_all()
        self.assertTrue(s.handle('UP'))
        self.assertEqual(ctx.bankroll.bet, 10)
        self.stack(s, ['TS', '9D', '6H', '8C', 'KD'])
        s.handle('A')
        self.assertEqual(s.table.state, PLAYING)
        s.handle('A')                       # hit, bust
        self.assertEqual(s.table.state, RESULT)
        self.assertEqual(ctx.bankroll.balance, 990)
        self.assertEqual(ctx.store.load(), (990, None))   # saved once per round
        s.handle('A')                       # next hand
        self.assertEqual(s.table.state, BETTING)
        self.assertFalse(s.handle('B'))     # leave to menu

    def test_with_art_and_double_and_broke(self):
        write_565(os.path.join(self.adir, 'table.565'), 240, 240, (0, 90, 40))
        write_sheet(self.adir, 'cards', {card_from_name('5S'): (240, 232, 200), 52: (30, 60, 160)})
        write_sheet(self.adir, 'chips', {1: (200, 20, 20)})
        write_sheet(self.adir, 'banners', {0: (240, 200, 60)})
        ctx = make_ctx(self.adir, self.sdir, balance=20)
        s = blackjack.Screen(ctx)
        self.assertTrue(s.has_table_art)
        self.assertEqual(set(ctx.assets.open_sheets), {'cards', 'chips', 'banners'})
        s.draw_all()
        # the player's first card (5S) comes from the cards sheet
        px = s.lcd.pixel(12 + 20, blackjack.PLAYER_Y + 30)
        s.table.shoe = Shoe(6, random.Random(0), stacked=[card_from_name(n) for n in ['5S', 'TD', '6H', '8C', 'TH']])
        s.table.deal()
        s.draw_all()
        found = any(s.lcd.pixel(x, blackjack.PLAYER_Y + 30) == rgb(240, 232, 200) for x in range(12, 228))
        self.assertTrue(found, 'card from sheet not drawn')
        s.table.round = None
        s.table.state = BETTING
        ctx.bankroll.bet = 5
        s.draw_all()
        self.stack(s, ['5S', 'TD', '6H', '8C', 'TH'])
        s.handle('A')                        # deal, bet 5
        self.assertTrue(s.table.can_double())
        s.handle('X')                        # double, win 10
        self.assertEqual(s.table.state, RESULT)
        self.assertEqual(ctx.bankroll.balance, 30)
        s.handle('A')
        # lose it all: bet up to 30 then bust
        for _ in range(6):
            s.handle('UP')
        self.assertEqual(ctx.bankroll.bet, 30)
        self.stack(s, ['TS', '9D', '6H', '8C', 'KD'])
        s.handle('A')
        s.handle('A')
        self.assertEqual(ctx.bankroll.balance, 0)
        s.handle('A')
        self.assertEqual(s.table.state, BROKE)
        s.handle('A')                        # refill
        self.assertEqual((s.table.state, ctx.bankroll.balance), (BETTING, 1000))
        self.assertEqual(ctx.store.load(), (1000, None))

    def test_blackjack_on_deal_and_shuffle_moment(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = blackjack.Screen(ctx)
        s.table.shoe.pos = 300               # force a reshuffle on the next deal
        s.handle('A')
        self.assertTrue(s.table.shuffled)
        s.handle('A' if s.table.state == RESULT else 'B')
        # stacked blackjack
        s.table.next_hand() if s.table.state == RESULT else None
        self.stack(s, ['AS', '9D', 'KH', '7C'])
        s.handle('A')
        self.assertEqual(s.table.state, RESULT)
        s.draw_bottom()

    def test_many_random_keys_never_crash(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = blackjack.Screen(ctx)
        rng = random.Random(11)
        keys = ['A', 'B', 'X', 'Y', 'UP', 'DOWN', 'LEFT', 'RIGHT', 'PRESS']
        alive = True
        for _ in range(600):
            k = rng.choice(keys)
            if k == 'B' and s.table.state in (BETTING, RESULT, BROKE):
                continue
            alive = s.handle(k)
            self.assertTrue(alive)
            if s.table.state == BROKE:
                s.handle('A')


class Entry(unittest.TestCase):
    def test_pocket_compiles_and_menu_draws(self):
        # pocket.py runs main() when executed; import it with main guarded by a fake __name__
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, 'pocket.py')) as f:
            src = f.read()
        src = src.replace('\nmain()\n', '\n')
        ns = {'__name__': 'pocket_test'}
        exec(compile(src, 'pocket.py', 'exec'), ns)
        adir = tempfile.mkdtemp()
        try:
            ctx = ns['Ctx']()
            ctx.assets = Assets(adir)
            ctx.bankroll = Bankroll()
            ns['message']('hello\nworld', 0)
            ns['draw_menu'](ctx, 0)
            ns['draw_menu'](ctx, 2)
            self.assertEqual(ns['menu_select'](ctx, 2, 1, 0), 0)
            self.assertIn((125000000, 125000000), machine.freq_calls)      # DR-050 boot call
            lcd = ns['lcd']
            # no background art: style A (DR-072): shaded felt in the margin, gold border lines, the
            # selected row a pill in its game's colour with a gold chip cursor in the right margin,
            # unselected rows the darker shade, a code-drawn suit sign in the icon slot
            self.assertEqual(lcd.pixel(2, 100), ns['SHADES'][25])
            self.assertEqual(lcd.pixel(4, 100), ns['GOLD'])
            self.assertEqual(lcd.pixel(120, ns['ROW_Y'][1] + 2), ns['GAME_COLOUR']['holdem'][0])
            self.assertEqual(lcd.pixel(120, ns['ROW_Y'][0] + 2), ns['GAME_COLOUR']['blackjack'][1])
            self.assertEqual(lcd.pixel(ns['ROW_X'] + ns['ROW_W'] + 5, ns['ROW_Y'][1] + 24), ns['GOLD'])
            self.assertNotEqual(lcd.pixel(ns['ROW_X'] + ns['ROW_W'] + 5, ns['ROW_Y'][0] + 24), ns['GOLD'])
            self.assertEqual(lcd.pixel(ns['ROW_X'] + 28, ns['ROW_Y'][0] + 24), ns['CREAM'])      # spade body
            self.assertEqual(lcd.pixel(ns['ROW_X'] + 28, ns['ROW_Y'][1] + 24), ns['SUIT_RED'])   # diamond
            self.assertEqual(lcd.pixel(ns['ROW_X'] + 28, ns['ROW_Y'][2] + 24 - 7), ns['CREAM'])  # club top leaf
            # with John's background: the photo shows in the margin and inside unselected rows,
            # the plates and the selected row cover it under the text
            write_565(os.path.join(adir, 'menu_background.565'), 240, 240, (200, 40, 80))
            photo = rgb(200, 40, 80)
            ctx.assets = Assets(adir)
            del ctx.menu_art
            ns['draw_menu'](ctx, 0)
            self.assertEqual(lcd.pixel(2, 100), photo)
            self.assertEqual(lcd.pixel(ns['ROW_X'] + 2, ns['ROW_Y'][0] + 2), ns['PANEL'])
            self.assertEqual(lcd.pixel(ns['ROW_X'] + 2, ns['ROW_Y'][1] + 2), photo)
            bx, by, bw, bh = ns['label_box'](1, 1)
            self.assertEqual(lcd.pixel(bx, by), ns['PLATE'])
            ns['menu_select'](ctx, 0, 1, 0)
            self.assertEqual(lcd.pixel(ns['ROW_X'] + 2, ns['ROW_Y'][0] + 2), photo)
            self.assertEqual(lcd.pixel(ns['ROW_X'] + 2, ns['ROW_Y'][1] + 2), ns['PANEL'])
            self.assertEqual(lcd.pixel(2, 100), photo)
            for i in range(len(ns['MENU'])):
                slot = i % ns['VISIBLE']
                bx, by, bw, bh = ns['label_box'](i, slot)
                lx = ns['label_x'](i)
                self.assertTrue(bx <= lx and lx + ns['label_width'](i) <= bx + bw, i)     # plate holds the label
                self.assertTrue(ns['ROW_X'] <= bx and bx + bw <= ns['ROW_X'] + ns['ROW_W'], i)
                self.assertTrue(ns['ROW_Y'][slot] <= by and by + bh <= ns['ROW_Y'][slot] + ns['ROW_H'], i)
            # scrolling (DR-022): walk down the whole list and back up; the window follows the selection
            n = len(ns['MENU'])
            self.assertGreater(n, ns['VISIBLE'])
            top = 0
            ns['draw_menu'](ctx, 0, top)
            for sel in range(1, n):
                top = ns['menu_select'](ctx, sel - 1, sel, top)
                self.assertTrue(top <= sel < top + ns['VISIBLE'], (sel, top))
            self.assertEqual(top, n - ns['VISIBLE'])
            # down arrow gone at the end, up arrow present: the gold glyph sits in the margin column
            ax = ns['ROW_X'] + ns['ROW_W'] + 4
            self.assertEqual(lcd.pixel(ax, ns['ROW_Y'][0] + 2), ns['GOLD'])
            self.assertNotEqual(lcd.pixel(ax, ns['ROW_Y'][2] + ns['ROW_H'] - 10), ns['GOLD'])
            for sel in range(n - 2, -1, -1):
                top = ns['menu_select'](ctx, sel + 1, sel, top)
            self.assertEqual(top, 0)
            self.assertEqual(lcd.pixel(ax, ns['ROW_Y'][2] + ns['ROW_H'] - 10), ns['GOLD'])   # down arrow back
            self.assertNotEqual(lcd.pixel(ax, ns['ROW_Y'][0] + 2), ns['GOLD'])
            self.assertEqual(ns['top_for'](4, 0), 2)
            self.assertEqual(ns['top_for'](0, 2), 0)
            self.assertEqual(ns['top_for'](3, 2), 2)
            # menu geometry: labels end inside the row box, rows do not overlap, footer is clear
            rows = ns['ROW_Y']
            box_l, box_r = ns['ROW_X'], ns['ROW_X'] + ns['ROW_W']
            self.assertGreaterEqual(box_l, 0)
            self.assertLessEqual(box_r, 240)
            self.assertLessEqual(box_r + 4 + 8, 240)                          # scroll arrow column fits
            area_centre = (ns['LABEL_X0'] + box_r) // 2
            for i, (label, mod, icon) in enumerate(ns['MENU']):
                lx = ns['label_x'](i)
                w = font.width(label, 2)
                self.assertLessEqual(len(label), 9, label)                   # 9 x 16 px fits the 152 px label area
                self.assertGreaterEqual(lx, ns['LABEL_X0'], label)          # clear of the icon slot
                self.assertLessEqual(lx + w, box_r, label)                   # inside the box
                self.assertLessEqual(abs((lx + w // 2) - area_centre), 1, label)   # centred in the box
            for i in range(1, len(rows)):
                self.assertGreaterEqual(rows[i], rows[i - 1] + ns['ROW_H'])
            self.assertEqual(len(rows), ns['VISIBLE'])
            self.assertGreaterEqual(rows[0], 40 + 16 + 8)          # below the balance line
            self.assertLessEqual(rows[-1] + ns['ROW_H'], 226 - 4)   # above the footer
            self.assertLessEqual(font.width('Pocket Chance', 2), 240)
        finally:
            shutil.rmtree(adir)


if __name__ == '__main__':
    unittest.main()
