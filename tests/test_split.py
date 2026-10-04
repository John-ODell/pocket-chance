"""Splitting pairs (DR-016 option B): engine, table and screen."""
import os
import random
import shutil
import sys
import tempfile
import unittest

import tests.context  # noqa: F401
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fakes'))
from cards import card_from_name, Shoe, hand_value  # noqa: E402
from bankroll import Bankroll  # noqa: E402
from blackjack_rules import Rules, Round, WIN, LOSE, PUSH, BUST, BLACKJACK, PLAYER, DONE  # noqa: E402
from blackjack_table import Table, PLAYING, RESULT  # noqa: E402


def h(*names):
    return [card_from_name(n) for n in names]


def rnd(order, bet=10, rules=None):
    rules = rules or Rules()
    return Round(Shoe(6, random.Random(0), stacked=h(*order)), rules, bet).deal()


def table(order, balance=1000, bet=10, rules=None):
    t = Table(random.Random(0), rules, bankroll=Bankroll(balance))
    t.shoe = Shoe(6, random.Random(0), stacked=h(*order))
    t.adjust_bet(bet - t.bankroll.bet)
    return t


class CanSplit(unittest.TestCase):
    def test_same_rank_only(self):
        self.assertTrue(rnd(['8S', '5D', '8H', '9C']).can_split())
        self.assertTrue(rnd(['KS', '5D', 'KH', '9C']).can_split())
        self.assertFalse(rnd(['KS', '5D', 'QH', '9C']).can_split())     # ten-value but different rank
        self.assertFalse(rnd(['8S', '5D', '7H', '9C']).can_split())

    def test_only_before_acting_and_only_once(self):
        r = rnd(['8S', '5D', '8H', '9C', '2D', '3D', '4D', '5C', '6C'])
        r.hit()
        self.assertFalse(r.can_split())
        r = rnd(['8S', '5D', '8H', '9C', '8D', '8C', '2D', '3D', '4D', '5C'])
        r.split()
        self.assertFalse(r.can_split())           # 8,8 again on the first hand: no re-split
        with self.assertRaises(ValueError):
            r.split()

    def test_rule_switch(self):
        self.assertFalse(rnd(['8S', '5D', '8H', '9C'], rules=Rules(allow_split=False)).can_split())

    def test_not_after_blackjack_or_when_done(self):
        r = rnd(['AS', '5D', 'KH', '9C'])
        self.assertEqual(r.state, DONE)
        self.assertFalse(r.can_split())


class SplitPlay(unittest.TestCase):
    # deal order: player, dealer up, player, dealer hole, then: hand-1 card, hand-2 card, draws...
    def test_one_card_to_each_hand_and_stake_doubles(self):
        r = rnd(['8S', '5D', '8H', '9C', '2D', '3D'])
        r.split()
        self.assertEqual([len(x) for x in r.hands], [2, 2])
        self.assertEqual(hand_value(r.hands[0])[0], 10)
        self.assertEqual(hand_value(r.hands[1])[0], 11)
        self.assertEqual((r.bets, r.bet), ([10, 10], 20))
        self.assertEqual((r.state, r.active), (PLAYER, 0))
        self.assertTrue(r.is_split)

    def test_hands_play_in_order(self):
        r = rnd(['8S', '5D', '8H', '9C', '2D', '3D', 'TS', '9S', 'TD'])
        r.split()
        r.hit()                                    # hand 1: 8+2+T = 20
        self.assertEqual(r.active, 0)
        r.stand()
        self.assertEqual(r.active, 1)
        r.hit()                                    # hand 2: 8+3+9 = 20
        self.assertEqual(r.active, 1)
        r.stand()
        self.assertEqual(r.state, DONE)
        self.assertEqual(r.outcomes, [WIN, WIN])   # dealer 5+9 = 14 -> draws T -> 24
        self.assertEqual(r.net, 20)

    def test_bust_on_first_hand_moves_on(self):
        r = rnd(['8S', '5D', '8H', '9C', '7D', '3D', 'TS', '7C'])
        r.split()
        r.hit()                                    # hand 1: 8+7+T = 25 bust
        self.assertEqual((r.outcomes[0], r.active, r.state), (BUST, 1, PLAYER))
        r.stand()                                  # hand 2: 11 stands; dealer 14 draws 7 -> 21
        self.assertEqual(r.outcomes, [BUST, LOSE])
        self.assertEqual(r.net, -20)

    def test_both_bust_dealer_does_not_draw(self):
        r = rnd(['8S', '5D', '8H', '9C', '7D', '7C', 'TS', 'TD', 'KD'])
        r.split()
        r.hit()
        r.hit()
        self.assertEqual((r.state, r.outcomes), (DONE, [BUST, BUST]))
        self.assertEqual(len(r.dealer), 2)
        self.assertEqual((r.outcome, r.net), (BUST, -20))

    def test_mixed_results_and_overall_outcome(self):
        # hand 1: 8+T = 18 stand; hand 2: 8+3 -> hit 9 = 20 stand; dealer 5+9=14 -> draws 5 -> 19
        r = rnd(['8S', '5D', '8H', '9C', 'TS', '3D', '9D', '5C'])
        r.split()
        r.stand()
        r.hit()
        r.stand()
        self.assertEqual(r.outcomes, [LOSE, WIN])
        self.assertEqual((r.nets, r.net, r.outcome), ([-10, 10], 0, PUSH))

    def test_21_after_split_pays_even_money_and_stands_itself(self):
        # hand 1: 8+K = 18? use tens: K,K split -> K+A = 21, K+5 = 15
        r = rnd(['KS', '5D', 'KH', '9C', 'AD', '5C', '3D', 'TD'])
        r.split()
        self.assertEqual(r.active, 1)              # hand 1 is 21, skipped automatically
        r.hit()                                    # hand 2: 15 + 3 = 18
        r.stand()                                  # dealer 14 -> T -> 24 bust
        self.assertEqual(r.outcomes, [WIN, WIN])
        self.assertEqual(r.nets, [10, 10])          # 21 after a split is not blackjack
        self.assertNotIn(BLACKJACK, r.outcomes)

    def test_split_aces_one_card_each_then_dealer_plays(self):
        r = rnd(['AS', '5D', 'AH', '9C', 'TD', '5C', 'TS'])
        r.split()
        self.assertEqual(r.state, DONE)             # no decisions left
        self.assertEqual([hand_value(x)[0] for x in r.hands], [21, 16])
        self.assertEqual(len(r.dealer), 3)          # dealer 14 drew a ten -> 24
        self.assertEqual(r.outcomes, [WIN, WIN])
        self.assertEqual(r.net, 20)

    def test_double_after_split(self):
        r = rnd(['8S', '5D', '8H', '9C', '3D', '2D', 'TS', 'TD', 'KD'])
        r.split()                                  # hands 11 and 10
        self.assertTrue(r.can_double())
        r.double()                                 # hand 1: 11 + T = 21, bet 20
        self.assertEqual((r.bets, r.doubled, r.active), ([20, 10], [True, False], 1))
        r.double()                                 # hand 2: 10 + T = 20, bet 20
        self.assertEqual(r.bets, [20, 20])
        self.assertEqual(r.state, DONE)            # dealer 14 + K = 24
        self.assertEqual(r.net, 40)

    def test_double_after_split_can_be_switched_off(self):
        r = rnd(['8S', '5D', '8H', '9C', '3D', '2D'], rules=Rules(double_after_split=False))
        r.split()
        self.assertFalse(r.can_double())

    def test_player_bet_properties_follow_active_hand(self):
        r = rnd(['8S', '5D', '8H', '9C', '3D', '2D', 'TS', '4D', '5D'])
        r.split()
        self.assertEqual(hand_value(r.player)[0], 11)
        r.stand()
        self.assertEqual(hand_value(r.player)[0], 10)
        self.assertEqual(r.bet, 20)


class TableSplit(unittest.TestCase):
    def test_needs_bankroll_for_second_bet(self):
        t = table(['8S', '5D', '8H', '9C', '3D', '2D'], balance=20, bet=10)
        t.deal()
        self.assertTrue(t.can_split())
        t = table(['8S', '5D', '8H', '9C', '3D', '2D'], balance=19, bet=10)
        t.deal()
        self.assertFalse(t.can_split())
        with self.assertRaises(ValueError):
            t.split()
        self.assertEqual(t.state, PLAYING)

    def test_double_after_split_needs_more_bankroll(self):
        t = table(['8S', '5D', '8H', '9C', '3D', '2D'], balance=25, bet=10)
        t.deal()
        t.split()                                  # 20 at stake, 25 in bankroll
        self.assertFalse(t.can_double())           # would need 30
        t = table(['8S', '5D', '8H', '9C', '3D', '2D'], balance=30, bet=10)
        t.deal()
        t.split()
        self.assertTrue(t.can_double())

    def test_stakes_and_balance(self):
        t = table(['8S', '5D', '8H', '9C', 'TS', '3D', '9D', '5C'])
        t.deal()
        self.assertEqual(t.stakes(), (990, 10))
        t.split()
        self.assertEqual(t.stakes(), (980, 20))
        t.stand()
        t.hit()
        t.stand()
        self.assertEqual((t.state, t.bankroll.balance), (RESULT, 1000))   # lose 10, win 10
        self.assertEqual(t.stakes(), (1000, 20))
        t.next_hand()
        self.assertEqual(t.bankroll.bet, 10)


class ScreenSplit(unittest.TestCase):
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

    def test_y_splits_and_hands_play_through(self):
        s = self.screen
        s.draw_all()
        s.handle('UP')
        self.stack(['8S', '5D', '8H', '9C', 'TS', '3D', '9D', '5C'])
        s.handle('A')
        self.assertTrue(s.table.can_split())
        s.handle('Y')
        self.assertTrue(s.table.round.is_split)
        self.assertEqual(s.table.stakes(), (980, 20))
        s.handle('B')                              # hand 1 stands on 18
        s.handle('A')                              # hand 2 hits to 20
        s.handle('B')
        self.assertEqual(s.table.state, RESULT)
        self.assertEqual(self.ctx.store.load(), (1000, None))
        s.handle('A')

    def test_y_ignored_without_a_pair(self):
        s = self.screen
        self.stack(['8S', '5D', '7H', '9C', 'TS'])
        s.handle('A')
        self.assertTrue(s.handle('Y'))
        self.assertEqual((s.table.state, len(s.table.round.hands)), (PLAYING, 1))

    def test_split_aces_finish_on_y(self):
        s = self.screen
        self.stack(['AS', '5D', 'AH', '9C', 'TD', '5C', 'TS'])
        s.handle('A')
        s.handle('Y')
        self.assertEqual(s.table.state, RESULT)
        self.assertEqual(self.ctx.bankroll.balance, 1010)

    def test_long_split_hands_draw(self):
        s = self.screen
        self.stack(['2S', '5D', '2H', '9C', '2D', '2C', '3S', '3H', '3D', '3C', '4S', '4H', '4D', '4C', '5S', '5H', 'TS', 'TD'])
        s.handle('A')
        s.handle('Y')
        for _ in range(3):
            s.handle('A')                          # hand 1 to 4 cards
        s.handle('B')
        for _ in range(3):
            s.handle('A')
        s.handle('B')
        self.assertEqual([len(x) for x in s.table.round.hands], [5, 5])
        self.assertEqual(s.table.state, RESULT)


if __name__ == '__main__':
    unittest.main()
