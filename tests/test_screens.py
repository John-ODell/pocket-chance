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
import clocks  # noqa: E402
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


class Clocks(unittest.TestCase):
    def test_fix_is_idempotent(self):
        machine.mem32[clocks.CTRL] = 0x840
        self.assertFalse(clocks.is_fast())
        self.assertTrue(clocks.fast_peripherals())
        self.assertEqual(machine.mem32[clocks.CTRL], 0x800)
        self.assertTrue(clocks.is_fast())
        self.assertFalse(clocks.fast_peripherals())
        self.assertEqual(machine.mem32[clocks.CTRL], 0x800)


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
        write_565(os.path.join(self.adir, 'c_AS.565'), 40, 56, (240, 232, 200))
        write_565(os.path.join(self.adir, 'c_back.565'), 40, 56, (30, 60, 160))
        write_565(os.path.join(self.adir, 'chip_5.565'), 24, 24, (200, 20, 20))
        write_565(os.path.join(self.adir, 'banner_win.565'), 160, 32, (240, 200, 60))
        ctx = make_ctx(self.adir, self.sdir, balance=20)
        s = blackjack.Screen(ctx)
        self.assertTrue(s.has_table_art)
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
            ns['draw_menu'](ctx, 0)
            ns['draw_menu'](ctx, 2)
            ns['message']('hello\nworld', 0)
            self.assertTrue(clocks.is_fast())
            # menu geometry: labels end inside the row box, rows do not overlap, footer is clear
            rows = ns['ROW_Y']
            box_l, box_r = ns['ROW_X'], ns['ROW_X'] + ns['ROW_W']
            self.assertGreaterEqual(box_l, 0)
            self.assertLessEqual(box_r, 240)
            area_centre = (ns['LABEL_X0'] + box_r) // 2
            for i, (label, mod, icon) in enumerate(ns['MENU']):
                lx = ns['label_x'](i)
                w = font.width(label, 2) + (8 + font.width('soon', 1) if mod is None else 0)
                self.assertGreaterEqual(lx, ns['LABEL_X0'], label)          # clear of the icon slot
                self.assertLessEqual(lx + w, box_r, label)                   # inside the box
                self.assertLessEqual(abs((lx + w // 2) - area_centre), 1, label)   # centred in the box
                if i:
                    self.assertGreaterEqual(rows[i], rows[i - 1] + ns['ROW_H'])
            self.assertGreaterEqual(rows[0], 40 + 16 + 8)          # below the balance line
            self.assertLessEqual(rows[-1] + ns['ROW_H'], 226 - 4)   # above the footer
            self.assertLessEqual(font.width('Pocket Chance', 2), 240)
        finally:
            shutil.rmtree(adir)


if __name__ == '__main__':
    unittest.main()
