"""Headless run of the Ultimate Texas Hold'em screen under CPython with the fake machine/framebuf/utime."""
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
from holdem_rules import PREFLOP, FLOP, RIVER, WIN, LOSE, FOLD  # noqa: E402
from holdem_table import BETTING, RESULT, BROKE  # noqa: E402
import holdem  # noqa: E402


class Ctx:
    pass


def make_ctx(adir, sdir, balance=1000, seed=3, seats=4, hint=True):
    ctx = Ctx()
    ctx.lcd = LCD()
    ctx.buttons = Buttons()
    ctx.assets = Assets(adir)
    ctx.store = Store(os.path.join(sdir, 'save.json'))
    ctx.bankroll = Bankroll(balance)
    ctx.rng = random.Random(seed)
    ctx.uth_seats = seats
    ctx.uth_hint = hint
    return ctx


def stack(screen, player, dealer, board):
    out = [card_from_name(n) for n in (player + ' ' + dealer + ' ' + board).split()]
    out += [c for c in range(52) if c not in out]
    screen.table.shoe = Shoe(1, random.Random(0), stacked=out)


class HoldemScreen(unittest.TestCase):
    def setUp(self):
        self.adir = tempfile.mkdtemp()
        self.sdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.adir)
        shutil.rmtree(self.sdir)

    def record_pushes(self, s):
        pushes = []
        real = s.lcd.show_band
        s.lcd.show_band = lambda y, h: pushes.append((y, h)) or real(y, h)
        return pushes

    def test_check_check_raise_with_hint_and_reveal(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = holdem.Screen(ctx)
        s.draw_all()
        s.handle('UP')                                          # ante 10
        stack(s, '9S 9D', 'KH 2C', '4C 3H 7D QS JC')
        s.handle('A')                                           # deal
        self.assertEqual((s.table.state, s.dealer_shown), (PREFLOP, 0))
        self.assertEqual(s.table.stakes(), (980, 10, 0))
        # community and dealer cards face down
        self.assertEqual(s.lcd.pixel(holdem.COMM_X[0] + 20, holdem.COMM_Y + 28), holdem.BLUE)
        self.assertEqual(s.lcd.pixel(holdem.PAIR_X[0] + 20, holdem.DEALER_Y + 28), holdem.BLUE)
        pushes = self.record_pushes(s)
        s.handle('B')                                           # check: flop turns
        self.assertEqual(s.table.state, FLOP)
        self.assertIn((holdem.COMM_TOP, holdem.ROW_H), pushes)
        self.assertNotEqual(s.lcd.pixel(holdem.COMM_X[0] + 20, holdem.COMM_Y + 28), holdem.BLUE)
        self.assertEqual(s.lcd.pixel(holdem.COMM_X[3] + 20, holdem.COMM_Y + 28), holdem.BLUE)     # turn still down
        s.handle('B')                                           # check: turn and river, hint computed
        self.assertEqual(s.table.state, RIVER)
        self.assertIsNotNone(s.table.outs)
        self.assertNotEqual(s.lcd.pixel(holdem.COMM_X[4] + 20, holdem.COMM_Y + 28), holdem.BLUE)
        pushes.clear()
        s.handle('A')                                           # raise 1x: showdown
        self.assertEqual(s.table.state, RESULT)
        self.assertEqual(s.table.round.outcome, WIN)
        self.assertEqual(pushes.count((holdem.DEALER_TOP, holdem.ROW_H)), 1)   # first card by band, second with the result
        self.assertEqual(s.dealer_shown, 2)
        self.assertNotEqual(s.lcd.pixel(holdem.PAIR_X[1] + 20, holdem.DEALER_Y + 28), holdem.BLUE)
        self.assertEqual(ctx.store.load(), (ctx.bankroll.balance, None))
        self.assertTrue(all(d != 0 for d in s.table.seats.delta))
        s.handle('A')
        self.assertEqual((s.table.state, s.dealer_shown), (BETTING, 0))

    def test_preflop_4x_and_3x(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = holdem.Screen(ctx)
        stack(s, '9S 9D', 'KH 2C', '4C 3H 7D QS JC')
        s.handle('A')
        s.handle('A')                                           # 4x
        self.assertEqual((s.table.state, s.table.round.play_bet), (RESULT, 20))
        s.handle('A')
        stack(s, '9S 9D', 'KH 2C', '4C 3H 7D QS JC')
        s.handle('A')
        s.handle('Y')                                           # 3x
        self.assertEqual(s.table.round.play_bet, 15)

    def test_fold_at_the_river(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = holdem.Screen(ctx)
        stack(s, '9S 4D', 'KH KC', '5C 3H 7D QS JC')
        s.handle('A')
        s.handle('B')
        s.handle('B')
        s.handle('B')                                           # fold
        self.assertEqual((s.table.state, s.table.round.outcome, ctx.bankroll.balance), (RESULT, FOLD, 990))

    def test_seats_boxes_and_markers(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = holdem.Screen(ctx)
        s.draw_all()
        # a disc of the first seat's chip colour in the dealer-row left box
        bx = holdem.BOX_X[0] + (holdem.BOX_W - 24) // 2 + 12
        self.assertEqual(s.lcd.pixel(bx, holdem.DEALER_Y + 44 - 12), holdem.CHIP_COL[0])
        stack(s, '9S 9D', 'KH 2C', '4C 3H 7D QS JC')
        s.handle('A')
        s.handle('A')
        marks = [s.lcd.pixel(holdem.BOX_X[k] + holdem.BOX_W - 5, y + 3)
                 for y in (holdem.DEALER_Y, holdem.PLAYER_Y) for k in range(2)]
        self.assertTrue(all(m in (holdem.UP, holdem.DOWN) for m in marks), marks)

    def test_no_seats_shows_hand_names_and_hint_off(self):
        ctx = make_ctx(self.adir, self.sdir, seats=0, hint=False)
        s = holdem.Screen(ctx)
        stack(s, '9S 9D', 'KH 2C', '4C 3H 7D QS JC')
        s.handle('A')
        s.handle('B')
        s.handle('B')
        self.assertIsNone(s.table.outs)
        s.draw_all()
        self.assertEqual(s.table.seats.count, 0)

    def test_broke_and_refill(self):
        ctx = make_ctx(self.adir, self.sdir, balance=30)
        s = holdem.Screen(ctx)
        stack(s, '9S 4D', 'KH KC', '5C 3H 7D QS JC')
        s.handle('A')
        s.handle('A')                                           # 4x with a losing hand: -30
        self.assertEqual(ctx.bankroll.balance, 0)
        s.handle('A')
        self.assertEqual(s.table.state, BROKE)
        s.handle('A')
        self.assertEqual((s.table.state, ctx.bankroll.balance), (BETTING, 1000))

    def test_help_and_menu(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = holdem.Screen(ctx)
        a = machine.Pin.registry[dict(PINS)['A']]
        a.value(0)
        self.assertTrue(s.handle('X'))
        a.value(1)
        s.buttons.poll()
        self.assertFalse(s.handle('B'))

    def test_random_keys_never_crash(self):
        ctx = make_ctx(self.adir, self.sdir, seed=9)
        s = holdem.Screen(ctx)
        rng = random.Random(4)
        a = machine.Pin.registry[dict(PINS)['A']]
        for _ in range(200):
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


if __name__ == '__main__':
    unittest.main()
