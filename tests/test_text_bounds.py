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
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
import font  # noqa: E402
from lcd import LCD  # noqa: E402
from buttons import Buttons  # noqa: E402
from art import Assets  # noqa: E402
from save import Store  # noqa: E402
from bankroll import Bankroll  # noqa: E402
from cards import card_from_name, Shoe  # noqa: E402
import blackjack  # noqa: E402
from blackjack_rules import Round, Rules, BLACKJACK, WIN, LOSE, PUSH, BUST  # noqa: E402
from blackjack_table import BETTING, PLAYING, RESULT, BROKE  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Ctx:
    pass


class Bounds:
    """Wrap font.text: draw for real, record the call, and flag any string that leaves the screen.
    verify() then checks each line's first and last glyph pixel still hold the text colour, which
    catches a later fill or line drawn over it (John saw the lower half of "You 21" cut off)."""
    def __init__(self, real):
        self.real = real
        self.bad = []
        self.calls = 0
        self.drawn = []

    def __call__(self, fb, s, x, y, c, size=1):
        self.calls += 1
        w = font.width(s, size)
        h = font.CH * size
        if x < 0 or y < 0 or x + w > 240 or y + h > 240:
            self.bad.append('%r at (%d,%d) size %d spans x %d..%d y %d..%d' % (s, x, y, size, x, x + w, y, y + h))
        self.real(fb, s, x, y, c, size)
        if s.strip():
            self.drawn.append((fb, s, x, y, c, size))

    def reset(self):
        self.drawn = []

    def verify(self, where):
        # the fake glyph lights its top row and its diagonal, so (x, y) and the diagonal's last
        # pixel of the last character are always set when the text is intact
        for fb, s, x, y, c, size in self.drawn:
            if len(s) <= 2:
                continue        # rank and suit glyphs on code-drawn cards; overlapping cards hide them by design
            lx = x + (len(s) - 1) * 8 * size + 7 * size
            ly = y + 7 * size
            for px, py in ((x, y), (lx, ly), (x + 7 * size, ly)):
                if fb.pixel(px, py) != c:
                    self.bad.append('%s: %r at (%d,%d) size %d was drawn over at (%d,%d)' % (where, s, x, y, size, px, py))


class TextBounds(unittest.TestCase):
    def setUp(self):
        self.real = font.text
        self.bounds = Bounds(self.real)
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

    def full(self, s, where):
        self.bounds.reset()
        s.draw_all()
        self.bounds.verify(where)

    def band(self, s, where):
        self.bounds.reset()
        s.draw_player()
        s.draw_bottom()
        self.bounds.verify(where)

    def test_blackjack_screens(self):
        for balance in (5, 1000, 999999):
            ctx = self.ctx(balance)
            s = blackjack.Screen(ctx)
            t = s.table
            self.full(s, 'idle')                                # betting or broke
            if t.state == BROKE:
                continue
            t.adjust_bet(1000)                                 # biggest bet allowed
            self.full(s, 'max bet')
            # long hands: 8 cards each, soft total text, both states
            t.shoe = Shoe(6, random.Random(0), stacked=[card_from_name(n) for n in
                          ['AS', 'AD', '2H', '2C', '2D', '2S', 'AH', 'AC', '3S', '3H', '3D', '3C', '4S', '4H', '4D', '4C', '5S', '5H', '5D', '5C']])
            t.deal()
            self.full(s, 'dealt')
            self.bounds.reset()
            s.shuffling()
            self.bounds.verify('shuffling')
            while t.state == PLAYING and len(t.round.player) < 8:
                t.hit()
                self.band(s, 'hit %d cards' % len(t.round.player))
            self.full(s, 'long hand')
            # every outcome, doubled and not
            for outcome in (BLACKJACK, WIN, LOSE, PUSH, BUST):
                for doubled in (False, True):
                    r = Round(t.shoe, t.rules, 500)
                    r.player = [card_from_name('TS'), card_from_name('9H')]
                    r.dealer = [card_from_name('TD'), card_from_name('8C')]
                    r.doubled = [doubled]
                    if doubled:
                        r.bets = [1000]
                    r._finish([outcome])
                    t.round = r
                    t.state = RESULT
                    self.full(s, '%s doubled=%s' % (outcome, doubled))
                    self.band(s, '%s doubled=%s band' % (outcome, doubled))
            # split: two hands of 5 cards, doubled second hand, playing and result views
            for doubled in (False, True):
                t.shoe = Shoe(6, random.Random(0), stacked=[card_from_name(n) for n in
                              ['2S', '5D', '2H', '9C', '2D', '2C', '3S', '3H', '3D', '3C', '4S', '4H', '4D', '4C', '5S', '5H', 'TS', 'TD']])
                t.state = BETTING
                t.round = None
                t.bankroll.balance = 5000           # the earlier hands may have lost; a split needs 2x the bet
                t.deal()
                t.split()
                self.band(s, 'split dealt')
                r = t.round
                r.hands[0] += [card_from_name(n) for n in ['3S', '3H', '3D']]
                r.hands[1] += [card_from_name(n) for n in ['4S', '4H', '4D']]
                r.doubled[1] = doubled
                r.bets[1] = 2000 if doubled else 1000
                self.band(s, 'split long playing')
                self.full(s, 'split long playing full')
                r._settle()
                t.state = RESULT
                self.full(s, 'split result doubled=%s' % doubled)
            t.round = None
            t.state = BROKE
            self.full(s, 'broke')
        self.check()

    def test_menu_and_messages(self):
        with open(os.path.join(ROOT, 'pocket.py')) as f:
            src = f.read().replace('\nmain()\n', '\n')
        ns = {'__name__': 'pocket_bounds'}
        exec(compile(src, 'pocket.py', 'exec'), ns)
        for art in (False, True):
            if art:
                data, _ = __import__('convert_assets').to_565([(200, 40, 80)] * (240 * 240), 240, 240)
                with open(os.path.join(self.dir, 'menu_background.565'), 'wb') as f:
                    f.write(data)
            for balance in (0, 1000, 999999):
                ctx = self.ctx(balance)
                n = len(ns['MENU'])
                top = 0
                self.bounds.reset()
                ns['draw_menu'](ctx, 0, top)
                self.bounds.verify('menu entry art=%s' % art)
                for sel in list(range(1, n)) + list(range(n - 2, -1, -1)):
                    self.bounds.reset()
                    top = ns['menu_select'](ctx, sel + (1 if sel < top else -1) if False else sel, sel, top)
                    self.bounds.verify('menu sel=%d top=%d art=%s' % (sel, top, art))
                for t in range(n - ns['VISIBLE'] + 1):
                    self.bounds.reset()
                    ns['draw_menu'](ctx, t, t)
                    self.bounds.verify('menu full top=%d art=%s' % (t, art))
        from save import MSG_RESTORED, MSG_FRESH
        for m in (MSG_RESTORED, MSG_FRESH):
            self.bounds.reset()
            ns['message'](m, 0)
            self.bounds.verify(m)
        self.check()


if __name__ == '__main__':
    unittest.main()
