import unittest

import tests.context  # noqa: F401
from bankroll import Bankroll


class BankrollTests(unittest.TestCase):
    def test_defaults(self):
        b = Bankroll()
        self.assertEqual((b.balance, b.bet, b.min_bet, b.max_bet, b.step), (1000, 5, 5, 500, 5))

    def test_bet_clamped_to_limits(self):
        b = Bankroll()
        self.assertEqual(b.adjust_bet(-5), 5)
        self.assertEqual(b.adjust_bet(5), 10)
        self.assertEqual(b.adjust_bet(10000), 500)
        self.assertEqual(b.adjust_bet(-10000), 5)

    def test_bet_capped_by_balance_in_steps(self):
        b = Bankroll(balance=47)
        self.assertEqual(b.top_bet(), 45)
        self.assertEqual(b.adjust_bet(1000), 45)
        b = Bankroll(balance=7)
        self.assertEqual(b.adjust_bet(1000), 5)

    def test_clamp_bet_after_loss(self):
        b = Bankroll(balance=300)
        b.adjust_bet(250)
        b.apply(-270)
        self.assertEqual(b.clamp_bet(), 30)

    def test_broke_and_refill(self):
        b = Bankroll(balance=4)
        self.assertTrue(b.is_broke())
        b.refill()
        self.assertEqual((b.balance, b.bet), (1000, 5))
        self.assertFalse(b.is_broke())
        self.assertFalse(Bankroll(balance=5).is_broke())

    def test_double_needs_twice_the_bet(self):
        b = Bankroll(balance=100)
        self.assertTrue(b.can_cover_double(50))
        self.assertFalse(b.can_cover_double(55))

    def test_apply(self):
        b = Bankroll()
        b.apply(15)
        b.apply(-5)
        self.assertEqual(b.balance, 1010)


if __name__ == '__main__':
    unittest.main()
