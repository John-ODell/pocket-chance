"""Headless run of the baccarat screen under CPython with the fake machine/framebuf/utime."""
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
from baccarat_rules import PLAYER, BANKER, TIE  # noqa: E402
from baccarat_table import BETTING, RESULT, BROKE  # noqa: E402
import baccarat  # noqa: E402


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


def stack(screen, names):
    cards = [card_from_name(n) for n in names.split()]
    rest = [c for c in range(52) if c not in cards]
    screen.table.shoe = Shoe(1, random.Random(0), stacked=cards + rest)


class BaccaratScreen(unittest.TestCase):
    def setUp(self):
        self.adir = tempfile.mkdtemp()
        self.sdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.adir)
        shutil.rmtree(self.sdir)

    def test_deal_is_clocked_and_pays(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = baccarat.Screen(ctx)
        s.draw_all()
        s.handle('UP')                                             # stake 10
        s.handle('UP')                                             # stake 15
        s.handle('RIGHT')
        s.handle('RIGHT')                                          # Banker
        self.assertEqual(s.table.side, BANKER)
        self.assertEqual(s.lcd.pixel(baccarat.BOX_X[BANKER], baccarat.BOX_Y), baccarat.GOLD)
        stack(s, '4S 3H 2D 2C 8S')                                 # P 6 stands, B 5 draws an 8 -> 3: Player wins
        pushes = []
        real = s.lcd.show_band
        s.lcd.show_band = lambda y, h: pushes.append((y, h)) or real(y, h)
        shows = []
        real_show = s.lcd.show
        s.lcd.show = lambda: shows.append(1) or real_show()
        s.handle('A')
        self.assertEqual(s.table.state, RESULT)
        self.assertEqual(s.table.coup.winner, PLAYER)
        self.assertEqual(ctx.bankroll.balance, 985)
        self.assertEqual(ctx.store.load(), (985, None))
        self.assertEqual(s.shown, 5)
        # cards 1-4 each a hand-band push, P, B, P, B; the fifth (Banker's third) comes with the result redraw
        self.assertEqual(pushes, [(baccarat.PLAYER_TOP, baccarat.BAND_H), (baccarat.BANKER_TOP, baccarat.BAND_H)] * 2)
        self.assertEqual(len(shows), 2)                            # empty table, then the result
        # three Banker cards on the table, two Player cards
        self.assertEqual(s.lcd.pixel(baccarat.CARD_X[2] + 20, baccarat.BANKER_Y + 28), baccarat.CREAM)
        self.assertNotEqual(s.lcd.pixel(baccarat.CARD_X[2] + 20, baccarat.PLAYER_Y + 28), baccarat.CREAM)
        # history: one blue square
        self.assertEqual(s.lcd.pixel(baccarat.HIST_X0 + 2, baccarat.HIST_Y + 2), baccarat.SIDE_COLOURS[PLAYER])
        s.handle('A')                                              # deals again with the same bet
        self.assertEqual(s.table.state, RESULT)
        self.assertEqual(s.table.side, BANKER)
        self.assertEqual(s.table.bankroll.bet, 15)

    def test_top_line_during_the_deal(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = baccarat.Screen(ctx)
        s.handle('UP')                                             # stake 10 on Player
        stack(s, '9S KH TD 2C')                                    # Player natural 9
        seen = []
        real = s.lcd.show_band
        s.lcd.show_band = lambda y, h: seen.append(s.table.stakes(s.revealing())) or real(y, h)
        s.handle('A')
        self.assertTrue(all(st == (990, 10) for st in seen), seen)  # stake off, win not yet in
        self.assertEqual(s.table.stakes(s.revealing()), (1010, 10))

    def test_tie_texts_and_markers(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = baccarat.Screen(ctx)
        s.handle('RIGHT')                                          # Tie
        stack(s, '4S 3H 3D 4C')                                    # 7-7 tie
        s.handle('A')
        self.assertEqual((s.table.coup.winner, ctx.bankroll.balance), (TIE, 1040))
        marks = [s.lcd.pixel(baccarat.RAIL_X[i] + 2, baccarat.RAIL_Y + 5) for i in range(5)]
        self.assertEqual(marks, [baccarat.PUSH] * 5)              # every seat was on a side: push
        s.handle('LEFT')                                           # leaves the result and moves to Player
        self.assertEqual((s.table.state, s.table.side), (BETTING, PLAYER))
        self.assertTrue(all(s.lcd.pixel(baccarat.RAIL_X[i] + 2, baccarat.RAIL_Y + 5) == baccarat.PUSH for i in range(5)))

    def test_rail_markers_after_a_decided_coup(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = baccarat.Screen(ctx)
        stack(s, '9S KH TD 2C')                                    # Player wins
        s.handle('A')
        marks = [s.lcd.pixel(baccarat.RAIL_X[i] + 2, baccarat.RAIL_Y + 5) for i in range(5)]
        # seats: Banker, Player, Banker (follow), Player (against), Banker
        self.assertEqual(marks, [baccarat.DOWN, baccarat.UP, baccarat.DOWN, baccarat.UP, baccarat.DOWN])

    def test_broke_and_refill(self):
        ctx = make_ctx(self.adir, self.sdir, balance=5)
        s = baccarat.Screen(ctx)
        s.handle('RIGHT')
        s.handle('RIGHT')                                          # Banker
        stack(s, '9S KH TD 2C')                                    # Player wins: lose 5
        s.handle('A')
        self.assertEqual(ctx.bankroll.balance, 0)
        s.handle('A')
        self.assertEqual(s.table.state, BROKE)
        s.handle('A')
        self.assertEqual((s.table.state, ctx.bankroll.balance), (BETTING, 1000))

    def test_shuffle_message(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = baccarat.Screen(ctx)
        s.table.shoe.pos = 52 * 8 - 10                             # past the cut card
        pushes = []
        real = s.lcd.show_band
        s.lcd.show_band = lambda y, h: pushes.append((y, h)) or real(y, h)
        s.handle('A')
        self.assertTrue(s.table.shuffled)
        self.assertEqual(pushes[0], (baccarat.BOTTOM_TOP, baccarat.BAND_H))   # "Shuffling..." first

    def test_paytable_and_menu(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = baccarat.Screen(ctx)
        a = machine.Pin.registry[dict(PINS)['A']]
        a.value(0)
        self.assertTrue(s.handle('X'))
        a.value(1)
        s.buttons.poll()
        self.assertFalse(s.handle('B'))

    def test_random_keys_never_crash(self):
        ctx = make_ctx(self.adir, self.sdir, seed=9)
        s = baccarat.Screen(ctx)
        rng = random.Random(4)
        a = machine.Pin.registry[dict(PINS)['A']]
        for _ in range(300):
            k = rng.choice(['A', 'UP', 'DOWN', 'LEFT', 'RIGHT', 'Y', 'PRESS', 'X', 'B'])
            if k == 'B':
                continue
            if k == 'X':
                a.value(0)
            self.assertTrue(s.handle(k))
            a.value(1)
            s.buttons.poll()
            if s.table.state == BROKE:
                s.handle('A')

    def test_seat_setting_zero(self):
        ctx = make_ctx(self.adir, self.sdir)
        ctx.bac_seats = 0
        s = baccarat.Screen(ctx)
        s.draw_all()
        self.assertEqual(s.table.seats.count, 0)
        self.assertNotEqual(s.lcd.pixel(baccarat.RAIL_X[0] + 10, baccarat.RAIL_Y + 11), baccarat.SEAT_COLOURS[0])

    def test_sheets_opened_and_cards_drawn_from_them(self):
        from tests.test_screens import write_sheet
        write_sheet(self.adir, 'cards', {card_from_name('9S'): (200, 200, 200)})
        ctx = make_ctx(self.adir, self.sdir)
        s = baccarat.Screen(ctx)
        self.assertEqual(sorted(ctx.assets.open_sheets), ['cards'])      # chips sheet absent, cards open
        stack(s, '9S KH TD 2C')
        s.handle('A')
        self.assertEqual(s.lcd.pixel(baccarat.CARD_X[0] + 20, baccarat.PLAYER_Y + 28), rgb(200, 200, 200))


if __name__ == '__main__':
    unittest.main()
