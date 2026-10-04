"""Headless run of the Caribbean screen under CPython with the fake machine/framebuf/utime."""
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
from caribbean_rules import WIN, LOSE, PUSH, FOLD  # noqa: E402
from caribbean_table import BETTING, DECIDING, RESULT, BROKE  # noqa: E402
import caribbean  # noqa: E402


class Ctx:
    pass


def make_ctx(adir, sdir, balance=1000, seed=3, seats=4):
    ctx = Ctx()
    ctx.lcd = LCD()
    ctx.buttons = Buttons()
    ctx.assets = Assets(adir)
    ctx.store = Store(os.path.join(sdir, 'save.json'))
    ctx.bankroll = Bankroll(balance)
    ctx.rng = random.Random(seed)
    ctx.car_seats = seats
    return ctx


def stack(screen, player, dealer, board, seats=''):
    out = [card_from_name(n) for n in (player + ' ' + dealer + ' ' + board + ' ' + seats).split()]
    out += [c for c in range(52) if c not in out]
    screen.table.shoe = Shoe(1, random.Random(0), stacked=out)


def drawn_strings(screen):
    """Capture the strings drawn by the next draw calls."""
    import font
    seen = []
    real = font.text

    def spy(fb, s, x, y, c, size=1):
        seen.append(s)
        real(fb, s, x, y, c, size)
    font.text = spy
    return seen, lambda: setattr(font, 'text', real)


class CaribbeanScreen(unittest.TestCase):
    def setUp(self):
        self.adir = tempfile.mkdtemp()
        self.sdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.adir)
        shutil.rmtree(self.sdir)

    def pushes(self, s):
        pushes = []
        real = s.lcd.show_band
        s.lcd.show_band = lambda y, h: pushes.append((y, h)) or real(y, h)
        return pushes

    def test_deal_turns_the_flop_then_prompts(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = caribbean.Screen(ctx)
        s.draw_all()
        s.handle('UP')                                                 # ante 10
        stack(s, '9S 9H', '4D 4C', '2S 5H KD 7C 3S')
        pushes = self.pushes(s)
        seen, restore = drawn_strings(s)
        s.handle('A')
        restore()
        self.assertEqual((s.table.state, s.board_shown, s.dealer_shown), (DECIDING, 3, 0))
        self.assertEqual(pushes, [(caribbean.COMM_TOP, caribbean.ROW_H), (caribbean.BOTTOM_TOP, 240 - caribbean.BOTTOM_TOP)])
        self.assertIn('A high 40  Y low 20  B fold', seen)
        self.assertIn('ante 10', seen)
        # flop up, turn and river still backs, dealer backs
        self.assertNotEqual(s.lcd.pixel(caribbean.COMM_X[2] + 20, caribbean.COMM_Y + 28), caribbean.BLUE)
        self.assertEqual(s.lcd.pixel(caribbean.COMM_X[3] + 20, caribbean.COMM_Y + 28), caribbean.BLUE)
        self.assertEqual(s.lcd.pixel(caribbean.PAIR_X[0] + 20, caribbean.DEALER_Y + 28), caribbean.BLUE)
        self.assertEqual(s.table.stakes(), (990, 10, 0))

    def test_high_call_showdown_and_pay(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = caribbean.Screen(ctx)
        s.handle('UP')
        stack(s, '9S 9H', '4D 4C', '2S 5H KD 7C 3S')
        s.handle('A')
        pushes = self.pushes(s)
        seen, restore = drawn_strings(s)
        s.handle('A')                                                  # high: call 40
        restore()
        self.assertEqual((s.table.state, s.table.round.outcome), (RESULT, WIN))
        self.assertEqual(ctx.bankroll.balance, 1050)
        self.assertEqual(ctx.store.load(), (1050, None))
        # turn+river band, bottom band (prompt cleared), dealer card 1; card 2 with the result redraw
        self.assertEqual(pushes, [(caribbean.COMM_TOP, caribbean.ROW_H), (caribbean.BOTTOM_TOP, 36),
                                  (caribbean.DEALER_TOP, caribbean.ROW_H)])
        self.assertEqual((s.board_shown, s.dealer_shown), (5, 2))
        self.assertIn('WIN +50', seen)
        self.assertIn('you pair / dlr pair', seen)
        self.assertIn('ante 10 call 40', seen)
        s.handle('A')
        self.assertEqual((s.table.state, s.board_shown, s.dealer_shown), (BETTING, 0, 0))

    def test_low_call_fold_and_push_texts(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = caribbean.Screen(ctx)
        stack(s, '2S 3H', '5D 6C', '7S 8H KD 7C 9S')                   # dealer straight
        s.handle('A')
        seen, restore = drawn_strings(s)
        s.handle('Y')                                                  # low: call 10
        restore()
        self.assertEqual((s.table.round.outcome, ctx.bankroll.balance), (LOSE, 985))
        self.assertIn('LOSE -15', seen)
        s.handle('A')
        stack(s, '9S 9H', '4D 4C', '2S 5H KD 7C 3S')
        s.handle('A')
        seen, restore = drawn_strings(s)
        s.handle('B')                                                  # fold: the cards still turn
        restore()
        self.assertEqual((s.table.round.outcome, ctx.bankroll.balance), (FOLD, 980))
        self.assertEqual(s.dealer_shown, 2)
        self.assertIn('FOLD -5', seen)
        s.handle('A')
        stack(s, 'AS AH', '2D 3C', '7S 8H KD TC 4S')                   # dealer has no hand
        s.handle('A')
        seen, restore = drawn_strings(s)
        s.handle('A')
        restore()
        self.assertEqual((s.table.round.outcome, ctx.bankroll.balance), (PUSH, 980))
        self.assertIn('PUSH, no dealer hand', seen)

    def test_multiplier_banner_and_pay(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = caribbean.Screen(ctx)
        s.handle('UP')                                                 # ante 10
        stack(s, 'AS AH', '4D 4C', '7S 8H KD TC 2S', 'KS KH QS QH JS JH 9S 9H')
        s.handle('A')
        seen, restore = drawn_strings(s)
        s.handle('A')
        restore()
        self.assertTrue(s.table.armed)
        self.assertIn('x3 NEXT HAND  A next  B menu', seen)
        seen, restore = drawn_strings(s)
        s.handle('A')                                                  # next hand: betting with the banner
        restore()
        self.assertIn('x3 PAYOUT NEXT HAND', seen)
        stack(s, 'AS AH', '4D 4C', '7S 8H KD TC 2S', '5S 5H 6S 6H QS QH JS JH')
        seen, restore = drawn_strings(s)
        s.handle('A')
        restore()
        self.assertIn('a win pays x3 this hand', seen)
        seen, restore = drawn_strings(s)
        s.handle('Y')                                                  # low 20 + Ante 10, all x3
        restore()
        self.assertEqual(s.table.round.net, 90)
        self.assertIn('WIN +90 (x3)', seen)

    def test_broke_and_refill(self):
        ctx = make_ctx(self.adir, self.sdir, balance=25)
        s = caribbean.Screen(ctx)
        stack(s, '2S 3H', '5D 6C', '7S 8H KD 7C 9S')
        s.handle('A')
        s.handle('A')                                                  # high: lose 25
        self.assertEqual(ctx.bankroll.balance, 0)
        s.handle('A')
        self.assertEqual(s.table.state, BROKE)
        s.handle('A')
        self.assertEqual((s.table.state, ctx.bankroll.balance), (BETTING, 1000))

    def test_help_and_menu(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = caribbean.Screen(ctx)
        a = machine.Pin.registry[dict(PINS)['A']]
        a.value(0)
        self.assertTrue(s.handle('X'))
        a.value(1)
        s.buttons.poll()
        self.assertFalse(s.handle('B'))

    def test_random_keys_never_crash(self):
        for seats in (4, 0):
            ctx = make_ctx(self.adir, self.sdir, seed=9, seats=seats)
            s = caribbean.Screen(ctx)
            rng = random.Random(4)
            a = machine.Pin.registry[dict(PINS)['A']]
            for _ in range(300):
                k = rng.choice(['A', 'UP', 'DOWN', 'LEFT', 'RIGHT', 'Y', 'PRESS', 'X', 'B'])
                if k == 'B' and s.table.state != DECIDING:
                    continue
                if k == 'X':
                    a.value(0)
                self.assertTrue(s.handle(k))
                a.value(1)
                s.buttons.poll()
                if s.table.state == BROKE:
                    s.handle('A')

    def test_seats_drawn_and_markers(self):
        ctx = make_ctx(self.adir, self.sdir)
        s = caribbean.Screen(ctx)
        s.draw_all()
        x, y = caribbean.BOX_X[0], caribbean.DEALER_Y
        self.assertNotIn(s.lcd.pixel(x + caribbean.BOX_W - 4, y + 4), (caribbean.UP, caribbean.DOWN))
        stack(s, '9S 9H', '4D 4C', '2S 5H KD 7C 3S')
        s.handle('A')
        s.handle('A')
        marks = [s.lcd.pixel(caribbean.BOX_X[k] + caribbean.BOX_W - 4, yy + 4)
                 for yy in (caribbean.DEALER_Y, caribbean.PLAYER_Y) for k in range(2)]
        self.assertTrue(all(m in (caribbean.UP, caribbean.DOWN) for m in marks), marks)

    def test_sheets_opened(self):
        from tests.test_screens import write_sheet
        write_sheet(self.adir, 'cards', {card_from_name('9S'): (200, 200, 200)})
        ctx = make_ctx(self.adir, self.sdir)
        s = caribbean.Screen(ctx)
        self.assertIn('cards', ctx.assets.open_sheets)
        stack(s, '9S 9H', '4D 4C', '2S 5H KD 7C 3S')
        s.handle('A')
        self.assertEqual(s.lcd.pixel(caribbean.PAIR_X[0] + 20, caribbean.PLAYER_Y + 28), rgb(200, 200, 200))
        self.assertEqual(s.lcd.pixel(caribbean.PAIR_X[0] + 20, caribbean.DEALER_Y + 28), caribbean.BLUE)


if __name__ == '__main__':
    unittest.main()
