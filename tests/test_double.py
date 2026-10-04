"""Every step of the double-down path (John: "Double seems off")."""
import os
import random
import shutil
import sys
import tempfile
import unittest

import tests.context  # noqa: F401
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fakes'))
from cards import card_from_name, Shoe  # noqa: E402
from bankroll import Bankroll  # noqa: E402
from blackjack_rules import Rules, Round, WIN, LOSE, PUSH, BUST, BLACKJACK, PLAYER, DONE  # noqa: E402
from blackjack_table import Table, BETTING, PLAYING, RESULT  # noqa: E402


def h(*names):
    return [card_from_name(n) for n in names]


def rnd(order, bet=10, rules=None):
    rules = rules or Rules()
    return Round(Shoe(6, random.Random(0), stacked=h(*order)), rules, bet).deal()


def table(order, balance=1000, bet=10):
    t = Table(random.Random(0), bankroll=Bankroll(balance))
    t.shoe = Shoe(6, random.Random(0), stacked=h(*order))
    t.adjust_bet(bet - t.bankroll.bet)
    return t


class RoundDouble(unittest.TestCase):
    def test_only_on_first_two_cards(self):
        r = rnd(['2S', 'TD', '3H', '7C', '2D', '9D'])
        self.assertTrue(r.can_double())
        r.hit()
        self.assertFalse(r.can_double())
        with self.assertRaises(ValueError):
            r.double()

    def test_exactly_one_card_then_auto_stand(self):
        r = rnd(['5S', 'TD', '6H', '8C', '3H', '9D'])      # player 11, doubles, gets 3 -> 14
        r.double()
        self.assertEqual(len(r.player), 3)
        self.assertEqual(r.state, DONE)                   # no further hit possible
        with self.assertRaises(ValueError):
            r.hit()
        self.assertEqual(len(r.dealer), 2)                # dealer 18 stands

    def test_bet_is_doubled(self):
        r = rnd(['5S', 'TD', '6H', '8C', 'TH'])
        self.assertEqual(r.bet, 10)
        r.double()
        self.assertEqual((r.bet, r.doubled), (20, [True]))

    def test_pays_twice_on_win(self):
        r = rnd(['5S', 'TD', '6H', '8C', 'TH'])            # 21 v 18
        r.double()
        self.assertEqual((r.outcome, r.net), (WIN, 20))

    def test_loses_twice_on_bust_and_on_lower_total(self):
        r = rnd(['TS', 'TD', '6H', '8C', 'KD'])            # 16 + K = bust
        r.double()
        self.assertEqual((r.outcome, r.net), (BUST, -20))
        r = rnd(['5S', 'TD', '6H', '8C', '2H'])            # 13 v 18
        r.double()
        self.assertEqual((r.outcome, r.net), (LOSE, -20))

    def test_push_returns_nothing(self):
        r = rnd(['5S', 'TD', '6H', '8C', '7H'])            # 18 v 18
        r.double()
        self.assertEqual((r.outcome, r.net), (PUSH, 0))

    def test_21_after_double_is_not_blackjack(self):
        r = rnd(['5S', 'TD', '6H', '8C', 'TH'])
        r.double()
        self.assertEqual(r.outcome, WIN)                  # even money on 2x bet, not 3:2
        self.assertNotEqual(r.outcome, BLACKJACK)
        self.assertEqual(r.net, 20)

    def test_dealer_still_plays_out(self):
        r = rnd(['5S', '6D', '6H', 'TC', '9H', '9D'])      # player 20; dealer 16 draws 9 -> 25
        r.double()
        self.assertEqual(len(r.dealer), 3)
        self.assertEqual((r.outcome, r.net), (WIN, 20))


class TableDouble(unittest.TestCase):
    def test_bankroll_must_cover_second_bet(self):
        t = table(['5S', 'TD', '6H', '8C', 'TH'], balance=20, bet=10)
        t.deal()
        self.assertTrue(t.can_double())                   # exactly enough
        t = table(['5S', 'TD', '6H', '8C', 'TH'], balance=19, bet=10)
        t.deal()
        self.assertFalse(t.can_double())
        with self.assertRaises(ValueError):
            t.double()
        self.assertEqual(t.state, PLAYING)                # refused double leaves the hand playable

    def test_balance_moves_by_twice_the_bet(self):
        t = table(['5S', 'TD', '6H', '8C', 'TH'])
        t.deal()
        t.double()
        self.assertEqual((t.state, t.bankroll.balance), (RESULT, 1020))
        t = table(['TS', 'TD', '6H', '8C', 'KD'])
        t.deal()
        t.double()
        self.assertEqual(t.bankroll.balance, 980)

    def test_standing_bet_unchanged_for_next_hand(self):
        t = table(['5S', 'TD', '6H', '8C', 'TH'])
        t.deal()
        t.double()
        t.next_hand()
        self.assertEqual((t.state, t.bankroll.bet), (BETTING, 10))

    def test_stakes_shown_on_screen(self):
        t = table(['5S', 'TD', '6H', '8C', 'TH'])
        self.assertEqual(t.stakes(), (1000, 10))         # betting
        t.deal()
        self.assertEqual(t.stakes(), (990, 10))          # stake on the table
        t.double()
        self.assertEqual(t.stakes(), (1020, 20))         # doubled bet shown, balance settled
        t.next_hand()
        self.assertEqual(t.stakes(), (1020, 10))

    def test_stakes_after_plain_hit_and_bust(self):
        t = table(['TS', '9D', '6H', '8C', 'KD'])
        t.deal()
        t.hit()
        self.assertEqual(t.stakes(), (990, 10))


class ScreenDouble(unittest.TestCase):
    """X on the screen: ignored when a double is not allowed, otherwise one key finishes the hand."""

    def setUp(self):
        import blackjack
        from lcd import LCD
        from buttons import Buttons
        from art import Assets
        from save import Store
        self.dir = tempfile.mkdtemp()

        class Ctx:
            pass
        ctx = Ctx()
        ctx.lcd = LCD()
        ctx.buttons = Buttons()
        ctx.assets = Assets(self.dir)
        ctx.store = Store(os.path.join(self.dir, 'save.json'))
        ctx.bankroll = Bankroll(1000)
        ctx.rng = random.Random(1)
        self.screen = blackjack.Screen(ctx)
        self.ctx = ctx

    def tearDown(self):
        shutil.rmtree(self.dir)

    def stack(self, order):
        self.screen.table.shoe = Shoe(6, random.Random(0), stacked=h(*order))

    def test_x_doubles_and_finishes(self):
        s = self.screen
        s.draw_all()
        s.handle('UP')                                    # bet 5 -> 10
        self.stack(['5S', 'TD', '6H', '8C', 'TH'])
        s.handle('A')
        self.assertEqual(s.table.stakes(), (990, 10))
        self.assertTrue(s.handle('X'))
        self.assertEqual((s.table.state, self.ctx.bankroll.balance), (RESULT, 1020))
        self.assertEqual(s.table.stakes(), (1020, 20))
        self.assertEqual(self.ctx.store.load(), (1020, None))

    def test_x_after_hit_is_ignored(self):
        s = self.screen
        self.stack(['2S', 'TD', '3H', '7C', '2D', '9D', '5C'])
        s.handle('A')
        s.handle('A')                                     # hit: 7
        self.assertTrue(s.handle('X'))
        self.assertEqual(s.table.state, PLAYING)
        self.assertEqual(len(s.table.round.player), 3)    # X dealt nothing

    def test_y_and_press_do_nothing_in_play(self):
        s = self.screen
        self.stack(['2S', 'TD', '3H', '7C', '2D', '9D', '5C'])
        s.handle('A')
        for k in ('Y', 'PRESS', 'UP', 'DOWN', 'LEFT', 'RIGHT'):
            self.assertTrue(s.handle(k))
            self.assertEqual(len(s.table.round.player), 2)


if __name__ == '__main__':
    unittest.main()
