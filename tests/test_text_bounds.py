"""Every string drawn on every screen must fit on the 240 px panel (John: "the menu is a mess";
"Slots (soon)" at size 2 ran 44 px off the right edge). Wraps font.text to measure each call."""
import os
import random
import shutil
import sys
import tempfile
import unittest

import tests.context  # noqa: F401
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fakes'))
import font  # noqa: E402
from lcd import LCD  # noqa: E402
from buttons import Buttons  # noqa: E402
from art import Assets  # noqa: E402
from save import Store  # noqa: E402
from bankroll import Bankroll  # noqa: E402
from cards import card_from_name, Shoe  # noqa: E402
import blackjack  # noqa: E402
from blackjack_rules import Round, Rules, BLACKJACK, WIN, LOSE, PUSH, BUST  # noqa: E402
from blackjack_table import PLAYING, RESULT, BROKE  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Ctx:
    pass


class Bounds:
    """Replace font.text; record any string that leaves the screen."""
    def __init__(self):
        self.bad = []
        self.calls = 0

    def __call__(self, fb, s, x, y, c, size=1):
        self.calls += 1
        w = font.width(s, size)
        h = font.CH * size
        if x < 0 or y < 0 or x + w > 240 or y + h > 240:
            self.bad.append('%r at (%d,%d) size %d spans x %d..%d y %d..%d' % (s, x, y, size, x, x + w, y, y + h))


class TextBounds(unittest.TestCase):
    def setUp(self):
        self.real = font.text
        self.bounds = Bounds()
        font.text = self.bounds
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        font.text = self.real
        shutil.rmtree(self.dir)

    def ctx(self, balance):
        ctx = Ctx()
        ctx.lcd = LCD()
        ctx.buttons = Buttons()
        ctx.assets = Assets(self.dir)
        ctx.store = Store(os.path.join(self.dir, 'save.json'))
        ctx.bankroll = Bankroll(balance)
        ctx.rng = random.Random(2)
        return ctx

    def check(self):
        self.assertEqual(self.bounds.bad, [])
        self.assertGreater(self.bounds.calls, 0)

    def test_blackjack_screens(self):
        for balance in (5, 1000, 999999):
            ctx = self.ctx(balance)
            s = blackjack.Screen(ctx)
            t = s.table
            s.draw_all()                                       # betting or broke
            if t.state == BROKE:
                continue
            t.adjust_bet(1000)                                 # biggest bet allowed
            s.draw_all()
            # long hands: 8 cards each, soft total text, both states
            t.shoe = Shoe(6, random.Random(0), stacked=[card_from_name(n) for n in
                          ['AS', 'AD', '2H', '2C', '2D', '2S', 'AH', 'AC', '3S', '3H', '3D', '3C', '4S', '4H', '4D', '4C', '5S', '5H', '5D', '5C']])
            t.deal()
            s.draw_all()
            s.shuffling()
            while t.state == PLAYING and len(t.round.player) < 8:
                t.hit()
                s.draw_player()
                s.draw_bottom()
            s.draw_all()
            # every outcome, doubled and not
            for outcome in (BLACKJACK, WIN, LOSE, PUSH, BUST):
                for doubled in (False, True):
                    r = Round(t.shoe, t.rules, 500)
                    r.player = [card_from_name('TS'), card_from_name('9H')]
                    r.dealer = [card_from_name('TD'), card_from_name('8C')]
                    r.doubled = doubled
                    if doubled:
                        r.bet = 1000
                    r._finish(outcome)
                    t.round = r
                    t.state = RESULT
                    s.draw_all()
            t.round = None
            t.state = BROKE
            s.draw_all()
        self.check()

    def test_menu_and_messages(self):
        with open(os.path.join(ROOT, 'pocket.py')) as f:
            src = f.read().replace('\nmain()\n', '\n')
        ns = {'__name__': 'pocket_bounds'}
        exec(compile(src, 'pocket.py', 'exec'), ns)
        for balance in (0, 1000, 999999):
            ctx = self.ctx(balance)
            for sel in range(len(ns['MENU'])):
                ns['draw_menu'](ctx, sel)
        from save import MSG_RESTORED, MSG_FRESH
        ns['message'](MSG_RESTORED, 0)
        ns['message'](MSG_FRESH, 0)
        self.check()


if __name__ == '__main__':
    unittest.main()
