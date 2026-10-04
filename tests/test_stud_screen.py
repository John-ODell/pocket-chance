"""Headless run of the Caribbean Stud screen under CPython with the fake machine/framebuf/utime."""
import os
import random
import shutil
import sys
import tempfile
import unittest

import tests.context  # noqa: F401
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fakes'))
import machine  # noqa: E402
from pixfmt import rgb  # noqa: E402
from lcd import LCD  # noqa: E402
from buttons import Buttons, PINS  # noqa: E402
from art import Assets  # noqa: E402
from save import Store  # noqa: E402
from bankroll import Bankroll  # noqa: E402
from cards import card_from_name, Shoe  # noqa: E402
from stud_rules import WIN, LOSE, FOLD, NOQUALIFY  # noqa: E402
from stud_table import BETTING, DECIDING, RESULT, BROKE  # noqa: E402
import stud  # noqa: E402


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


def stack(screen, player, dealer):
    """Stack the player's and dealer's cards, then the rest of the deck for the seats."""
    out = []
    for p, d in zip(player.split(), dealer.split()):
        out += [card_from_name(p), card_from_name(d)]
    out += [c for c in range(52) if c not in out]
    screen.table.shoe = Shoe(1, random.Random(0), stacked=out)


class StudScreen(unittest.TestCase):
    def setUp(self):
        self.adir = tempfile.mkdtemp()
        self.sdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.adir)
        shutil.rmtree(self.sdir)

    def test_raise_reveals_and_pays(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = stud.Screen(ctx)
        s.draw_all()
        s.handle('UP')                                           # ante 10
        stack(s, '9S 9D 4C 3H 2S', 'AH KD 5C 3D 2D')
        s.handle('A')
        self.assertEqual((s.table.state, s.shown), (DECIDING, 1))
        self.assertEqual(s.table.stakes(), (990, 10, 0))
        # dealer hole cards are face down: card-back blue at the second dealer card
        self.assertEqual(s.lcd.pixel(stud.CARD_X[1] + 20, stud.DEALER_Y + 28), stud.BLUE)
        pushes = []
        real = s.lcd.show_band
        s.lcd.show_band = lambda y, h: pushes.append((y, h)) or real(y, h)
        s.handle('A')                                            # raise
        self.assertEqual(s.table.state, RESULT)
        self.assertEqual(s.table.round.outcome, WIN)
        self.assertEqual(ctx.bankroll.balance, 1030)
        self.assertEqual(ctx.store.load(), (1030, None))
        self.assertEqual(s.shown, 5)
        self.assertEqual(pushes.count((stud.DEALER_TOP, stud.BAND_H)), 3)   # cards 2, 3, 4 one by one; the 5th with the result
        self.assertNotEqual(s.lcd.pixel(stud.CARD_X[1] + 20, stud.DEALER_Y + 28), stud.BLUE)
        s.handle('A')
        self.assertEqual((s.table.state, s.shown), (BETTING, 1))

    def test_fold_reveals_all_at_once(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = stud.Screen(ctx)
        stack(s, 'QS JD 4C 3H 2S', 'AH KD 5C 3D 2D')
        s.handle('A')
        pushes = []
        real = s.lcd.show_band
        s.lcd.show_band = lambda y, h: pushes.append((y, h)) or real(y, h)
        s.handle('B')
        self.assertEqual((s.table.state, s.table.round.outcome, ctx.bankroll.balance), (RESULT, FOLD, 995))
        self.assertEqual(pushes, [])
        self.assertEqual(s.shown, 5)

    def test_no_qualify_and_lose_texts(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = stud.Screen(ctx)
        stack(s, '9S 9D 4C 3H 2S', 'KH 7D 5C 3D 2D')
        s.handle('A')
        s.handle('A')
        self.assertEqual(s.table.round.outcome, NOQUALIFY)
        s.handle('A')
        stack(s, '9S 9D 4C 3H 2S', 'KH KD 5C 3D 2D')
        s.handle('A')
        s.handle('A')
        self.assertEqual(s.table.round.outcome, LOSE)

    def test_broke_and_refill(self):
        ctx = make_ctx(self.adir, self.sdir, balance=15)
        s = stud.Screen(ctx)
        stack(s, '9S 9D 4C 3H 2S', 'KH KD 5C 3D 2D')
        s.handle('A')
        s.handle('A')                                            # lose 15
        self.assertEqual(ctx.bankroll.balance, 0)
        s.handle('A')
        self.assertEqual(s.table.state, BROKE)
        s.handle('A')
        self.assertEqual((s.table.state, ctx.bankroll.balance), (BETTING, 1000))

    def test_paytable_and_menu(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = stud.Screen(ctx)
        a = machine.Pin.registry[dict(PINS)['A']]
        a.value(0)
        self.assertTrue(s.handle('X'))
        a.value(1)
        s.buttons.poll()
        self.assertFalse(s.handle('B'))
        s.run_cleanup = None

    def test_random_keys_never_crash(self):
        ctx = make_ctx(self.adir, self.sdir, seed=9)
        s = stud.Screen(ctx)
        rng = random.Random(4)
        a = machine.Pin.registry[dict(PINS)['A']]
        for _ in range(300):
            k = rng.choice(['A', 'UP', 'DOWN', 'LEFT', 'RIGHT', 'Y', 'PRESS', 'X', 'B'])
            if k == 'B' and s.table.state in (BETTING, RESULT, BROKE):
                continue
            if k == 'X':
                a.value(0)
            self.assertTrue(s.handle(k))
            a.value(1)
            s.buttons.poll()
            if s.table.state == BROKE:
                s.handle('A')

    def test_rail_shows_stacks_and_markers(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = stud.Screen(ctx)
        s.draw_all()
        # five stacks of five lines at 1000 chips, no markers yet
        for i in range(5):
            x = stud.RAIL_X[i]
            self.assertEqual(s.lcd.pixel(x + 10, stud.RAIL_Y + 11), stud.SEAT_COLOURS[i])      # bottom line
            self.assertEqual(s.lcd.pixel(x + 10, stud.RAIL_Y + 11 - 8), stud.SEAT_COLOURS[i])  # fifth line
            self.assertNotEqual(s.lcd.pixel(x + 10, stud.RAIL_Y + 11 - 10), stud.SEAT_COLOURS[i])  # no sixth
            self.assertNotIn(s.lcd.pixel(x + 2, stud.RAIL_Y + 5), (stud.UP, stud.DOWN))
        s.handle('A')
        s.handle('A')                                                # raise: every seat settles
        marks = [s.lcd.pixel(stud.RAIL_X[i] + 2, stud.RAIL_Y + 5) for i in range(5)]
        self.assertTrue(all(m in (stud.UP, stud.DOWN) for m in marks), marks)
        for i in range(5):
            self.assertEqual((marks[i] == stud.UP), s.table.seats.delta[i] > 0)
        s.handle('A')                                                # next hand: betting, markers stay until the deal
        self.assertTrue(all(s.lcd.pixel(stud.RAIL_X[i] + 2, stud.RAIL_Y + 5) in (stud.UP, stud.DOWN) for i in range(5)))
        s.handle('A')                                                # deal clears them
        self.assertTrue(all(s.lcd.pixel(stud.RAIL_X[i] + 2, stud.RAIL_Y + 5) not in (stud.UP, stud.DOWN) for i in range(5)))

    def test_seat_setting_zero(self):
        ctx = make_ctx(self.adir, self.sdir)
        ctx.stud_seats = 0
        s = stud.Screen(ctx)
        s.draw_all()
        self.assertEqual(s.table.seats.count, 0)
        self.assertNotEqual(s.lcd.pixel(stud.RAIL_X[0] + 10, stud.RAIL_Y + 11), stud.SEAT_COLOURS[0])

    def test_sheets_opened_and_card_back_stays_code_drawn(self):
        from tests.test_screens import write_sheet
        write_sheet(self.adir, 'cards', {52: (1, 2, 3), card_from_name('9S'): (200, 200, 200)})
        ctx = make_ctx(self.adir, self.sdir)
        s = stud.Screen(ctx)
        self.assertIn('cards', ctx.assets.open_sheets)
        stack(s, '9S 9D 4C 3H 2S', 'KH KD 5C 3D 2D')
        s.handle('A')
        self.assertEqual(s.lcd.pixel(stud.CARD_X[1] + 20, stud.DEALER_Y + 28), stud.BLUE)   # not the sheet's back
        self.assertEqual(s.lcd.pixel(stud.CARD_X[0] + 20, stud.PLAYER_Y + 28), rgb(200, 200, 200))


if __name__ == '__main__':
    unittest.main()
