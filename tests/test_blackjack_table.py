import random
import unittest

import tests.context  # noqa: F401
from bankroll import Bankroll
from cards import card_from_name, Shoe, hand_value
from blackjack_rules import Rules, BUST, BLACKJACK, WIN
from blackjack_table import Table, BETTING, PLAYING, RESULT, BROKE


def stacked_table(names, balance=1000, bet=10, rules=None):
    t = Table(random.Random(0), rules, Bankroll(balance=balance))
    t.shoe = Shoe(t.rules.decks, random.Random(0), stacked=[card_from_name(n) for n in names])
    t.adjust_bet(bet - t.bankroll.bet)
    return t


class TableFlow(unittest.TestCase):
    def test_start_states(self):
        self.assertEqual(Table(random.Random(1)).state, BETTING)
        self.assertEqual(Table(random.Random(1), bankroll=Bankroll(balance=3)).state, BROKE)

    def test_win_updates_bankroll(self):
        t = stacked_table(['TS', 'TD', '9H', '8C'])
        t.deal()
        self.assertEqual(t.state, PLAYING)
        t.stand()
        self.assertEqual((t.state, t.round.outcome, t.bankroll.balance), (RESULT, WIN, 1010))

    def test_blackjack_finishes_on_deal_and_pays_3_to_2(self):
        t = stacked_table(['AS', '9D', 'KH', '7C'])
        t.deal()
        self.assertEqual((t.state, t.round.outcome, t.bankroll.balance), (RESULT, BLACKJACK, 1015))

    def test_bust_loses_bet(self):
        t = stacked_table(['TS', '9D', '6H', '8C', 'KD'])
        t.deal()
        t.hit()
        self.assertEqual((t.round.outcome, t.bankroll.balance), (BUST, 990))

    def test_double_charges_double(self):
        t = stacked_table(['5S', 'TD', '6H', '8C', 'TH'])
        t.deal()
        self.assertTrue(t.can_double())
        t.double()
        self.assertEqual(t.bankroll.balance, 1020)

    def test_double_refused_when_balance_too_low(self):
        t = stacked_table(['5S', 'TD', '6H', '8C', 'TH'], balance=15, bet=10)
        t.deal()
        self.assertFalse(t.can_double())
        with self.assertRaises(ValueError):
            t.double()

    def test_next_hand_and_broke_then_refill(self):
        t = stacked_table(['TS', '9D', '6H', '8C', 'KD'], balance=10, bet=10)
        t.deal()
        t.hit()                      # bust, balance 0
        self.assertEqual(t.state, RESULT)
        t.next_hand()
        self.assertEqual(t.state, BROKE)
        with self.assertRaises(ValueError):
            t.adjust_bet(5)
        t.refill()
        self.assertEqual((t.state, t.bankroll.balance), (BETTING, 1000))

    def test_bet_follows_balance_down(self):
        t = stacked_table(['TS', '9D', '6H', '8C', 'KD'], balance=100, bet=100)
        t.deal()
        t.hit()
        t.next_hand()
        self.assertEqual(t.state, BROKE)

    def test_reshuffle_flag_between_hands(self):
        t = Table(random.Random(2), Rules(penetration=0.1))
        t.shoe.pos = 40
        t.deal()
        self.assertTrue(t.shuffled)

    def test_wrong_state_calls(self):
        t = Table(random.Random(1))
        with self.assertRaises(ValueError):
            t.next_hand()
        with self.assertRaises(ValueError):
            t.refill()

    def test_many_random_hands_keep_balance_consistent(self):
        rng = random.Random(9)
        t = Table(rng)
        expected = t.bankroll.balance
        for _ in range(3000):
            if t.state == BROKE:
                t.refill()
                expected = t.bankroll.balance
            t.adjust_bet(rng.choice([-5, 0, 5, 25]))
            t.deal()
            while t.state == PLAYING:
                if hand_value(t.round.player)[0] < 16:
                    t.hit()
                else:
                    t.stand()
            expected += t.round.net
            self.assertEqual(t.bankroll.balance, expected)
            t.next_hand()


if __name__ == '__main__':
    unittest.main()
