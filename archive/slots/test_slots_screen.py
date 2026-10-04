"""Headless run of the slots screen under CPython with the fake machine/framebuf/utime modules."""
import os
import random
import shutil
import sys
import tempfile
import unittest

import tests.context  # noqa: F401
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fakes'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
from convert_assets import to_565  # noqa: E402
from pixfmt import rgb  # noqa: E402
from lcd import LCD  # noqa: E402
from buttons import Buttons  # noqa: E402
from art import Assets  # noqa: E402
from save import Store  # noqa: E402
from bankroll import Bankroll  # noqa: E402
from slots_rules import SYMBOLS, STAR, CHERRY  # noqa: E402
from slots_table import BETTING, RESULT, BROKE, SYM_PX  # noqa: E402
import slots  # noqa: E402

SYM_COLOURS = {s: (10 + 20 * s, 100, 200 - 20 * s) for s in range(8)}


def write_sym(adir, sym):
    data, _ = to_565([SYM_COLOURS[sym]] * (SYM_PX * SYM_PX), SYM_PX, SYM_PX)
    with open(os.path.join(adir, 'sym_%s.565' % SYMBOLS[sym]), 'wb') as f:
        f.write(data)


class Ctx:
    pass


def make_ctx(adir, sdir, balance=1000, seed=3):
    ctx = Ctx()
    ctx.lcd = LCD()
    ctx.buttons = Buttons()
    ctx.assets = Assets(adir)
    ctx.store = Store(os.path.join(sdir, 'save.json'))
    ctx.bankroll = Bankroll(balance)
    ctx.rng = random.Random(seed)
    return ctx


class SlotsScreen(unittest.TestCase):
    def setUp(self):
        self.adir = tempfile.mkdtemp()
        self.sdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.adir)
        shutil.rmtree(self.sdir)

    def window_colour(self, s, i):
        """Colour at the centre of window i in the framebuffer."""
        return s.lcd.pixel(slots.WIN_X[i] + SYM_PX // 2, slots.WIN_Y + SYM_PX // 2)

    def test_ram_plan_is_fallback_b(self):
        s = slots.Screen(make_ctx(self.adir, self.sdir))
        self.assertEqual(len(s.win), 3)
        self.assertEqual(sum(len(b) for b in s.win), 18816)

    def test_spin_without_art_lands_on_the_stops(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = slots.Screen(ctx)
        s.draw_all()
        s.handle('UP')                                   # bet 10
        bal = ctx.bankroll.balance
        s.handle('A')
        self.assertEqual(s.table.state, RESULT)
        win, label = s.table.last
        self.assertEqual(ctx.bankroll.balance, bal - 10 + win)
        self.assertEqual(ctx.store.load(), (ctx.bankroll.balance, None))     # saved once
        line = s.table.reels.line()
        for i in range(3):
            bg, ink = slots.STANDIN[line[i]]
            self.assertEqual(self.window_colour(s, i), rgb(*ink))             # inner square of the stand-in
            self.assertEqual(s.lcd.pixel(slots.WIN_X[i] + 8, slots.WIN_Y + 8), rgb(*bg))
        self.assertTrue(all(f is None for f in s.files))                      # no file left open

    def test_spin_with_art_streams_the_right_symbols(self):
        for sym in range(8):
            write_sym(self.adir, sym)
        ctx = make_ctx(self.adir, self.sdir, seed=11)
        s = slots.Screen(ctx)
        s.draw_all()
        for _ in range(5):
            if s.table.state == RESULT:
                s.table.next()
            if s.table.state == BROKE:
                s.table.refill()
            s.handle('A')
            line = s.table.reels.line()
            for i in range(3):
                self.assertEqual(self.window_colour(s, i), rgb(*SYM_COLOURS[line[i]]), (line, i))
                # every row of the window buffer is the final symbol: nothing half-scrolled
                fb = s.win_fb[i]
                for y in (0, 1, 27, 54, 55):
                    self.assertEqual(fb.pixel(3, y), rgb(*SYM_COLOURS[line[i]]), (i, y))
        self.assertTrue(all(f is None for f in s.files))

    def test_spin_from_symbols_sheet_opens_no_files(self):
        import sheets as sh
        import art as art_module
        w, h, names = sh.SHEETS['symbols']
        px = []
        for s in range(8):
            px.extend([SYM_COLOURS[s]] * (w * h))
        data, _ = to_565(px, w, h * 8)
        with open(os.path.join(self.adir, 'symbols.565'), 'wb') as f:
            f.write(data)
        ctx = make_ctx(self.adir, self.sdir, seed=11)
        s = slots.Screen(ctx)
        self.assertIsNotNone(s.sheet)
        opens = []
        real = art_module.Assets.open_sprite
        art_module.Assets.open_sprite = lambda self_, name: opens.append(name) or real(self_, name)
        try:
            s.draw_all()
            for _ in range(3):
                if s.table.state == RESULT:
                    s.table.next()
                s.handle('A')
                line = s.table.reels.line()
                for i in range(3):
                    self.assertEqual(self.window_colour(s, i), rgb(*SYM_COLOURS[line[i]]), (line, i))
                    fb = s.win_fb[i]
                    for y in (0, 1, 27, 54, 55):
                        self.assertEqual(fb.pixel(3, y), rgb(*SYM_COLOURS[line[i]]), (i, y))
        finally:
            art_module.Assets.open_sprite = real
        self.assertEqual(opens, [])                                   # no per-symbol file opened during spins
        self.assertTrue(all(f is None for f in s.files))

    def test_mixed_art_and_standins(self):
        write_sym(self.adir, CHERRY)
        write_sym(self.adir, STAR)
        ctx = make_ctx(self.adir, self.sdir, seed=5)
        s = slots.Screen(ctx)
        for _ in range(4):
            if s.table.state == RESULT:
                s.table.next()
            s.handle('A')
            line = s.table.reels.line()
            for i in range(3):
                want = rgb(*SYM_COLOURS[line[i]]) if line[i] in (CHERRY, STAR) else rgb(*slots.STANDIN[line[i]][1])
                self.assertEqual(self.window_colour(s, i), want)

    def test_result_then_a_spins_again_and_bet_change_leaves_result(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = slots.Screen(ctx)
        s.handle('A')
        n1 = s.table.reels.stops[:]
        s.handle('A')                                    # spin again straight from the result
        self.assertEqual(s.table.state, RESULT)
        s.handle('UP')
        self.assertEqual(s.table.state, BETTING)
        self.assertEqual(ctx.bankroll.bet, 10)

    def test_broke_and_refill(self):
        ctx = make_ctx(self.adir, self.sdir, balance=5)
        s = slots.Screen(ctx)
        s.draw_all()
        while s.table.state != BROKE:
            if s.table.state == RESULT:
                s.handle('A')
            else:
                s.handle('A')
            if ctx.bankroll.balance > 2000:
                break
        if s.table.state == BROKE:
            s.handle('UP')                               # ignored
            s.handle('A')
            self.assertEqual((s.table.state, ctx.bankroll.balance), (BETTING, 1000))

    def test_paytable_and_menu_exit(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = slots.Screen(ctx)
        import machine
        from buttons import PINS
        # wait_any() needs a key: press A before entering the paytable
        machine.Pin.registry[dict(PINS)['A']].value(0)
        self.assertTrue(s.handle('X'))
        machine.Pin.registry[dict(PINS)['A']].value(1)
        s.buttons.poll()
        self.assertFalse(s.handle('B'))

    def test_random_keys_never_crash(self):
        ctx = make_ctx(self.adir, self.sdir, seed=9)
        s = slots.Screen(ctx)
        rng = random.Random(4)
        import machine
        from buttons import PINS
        a = machine.Pin.registry[dict(PINS)['A']]
        for _ in range(80):
            k = rng.choice(['A', 'UP', 'DOWN', 'LEFT', 'RIGHT', 'Y', 'PRESS', 'X'])
            if k == 'X':
                a.value(0)
            self.assertTrue(s.handle(k))
            a.value(1)
            s.buttons.poll()
            if s.table.state == BROKE:
                s.handle('A')


if __name__ == '__main__':
    unittest.main()
