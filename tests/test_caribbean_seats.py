"""Caribbean chip-stack seats (DR-069): strategy, settling, the multiplier condition."""
import random
import unittest

import tests.context  # noqa: F401
from cards import Shoe, card_from_name
from poker import evaluate
from caribbean_rules import Rules
from caribbean_seats import Seats, START


def cards(names):
    return [card_from_name(n) for n in names.split()]


class SeatsLogic(unittest.TestCase):
    def test_deal_uses_the_shared_deck(self):
        shoe = Shoe(1, random.Random(1), penetration=0.0)
        seen = [shoe.draw() for _ in range(9)]
        seats = Seats(4)
        seats.deal(shoe)
        allc = seen + [c for h in seats.hands for c in h]
        self.assertEqual(len(allc), 17)
        self.assertEqual(len(set(allc)), 17)

    def test_count_clamped(self):
        self.assertEqual(Seats(9).count, 4)
        self.assertEqual(Seats(-1).count, 0)
        s = Seats(0)
        self.assertTrue(s.all_won())                                  # vacuous; the table checks count > 0

    def test_act_and_settle(self):
        rules = Rules()
        seats = Seats(3)
        seats.hands = [cards('9S 9H'), cards('2S 3H'), cards('AS 4H')]
        flop = cards('KD 5C 8S')
        seats.act(flop, rules)
        self.assertEqual(seats.calls, [4, 0, 2])
        self.assertEqual([seats.status(i) for i in range(3)], ['4x', 'fold', '2x'])
        board = flop + cards('7C 2D')
        dv = evaluate(cards('6S 6H') + board)                         # pair of 6s: qualifies
        seats.settle(board, dv, 10, rules)
        # 9s beat 6s: Ante 10 + call 40; fold -10; ace high loses Ante + 20
        self.assertEqual(seats.delta, [50, -10, -30])
        self.assertEqual(seats.won, [True, False, False])
        self.assertFalse(seats.all_won())
        seats.deal(Shoe(1, random.Random(2), penetration=0.0))
        self.assertEqual(seats.delta, [0, 0, 0])

    def test_multiplier_applies_to_the_seats_too(self):
        rules = Rules()
        seats = Seats(1)
        seats.hands = [cards('9S 9H')]
        board = cards('KD 5C 8S 7C 2D')
        seats.act(board[:3], rules)
        seats.settle(board, evaluate(cards('6S 6H') + board), 10, rules, mult=3)
        self.assertEqual(seats.delta, [(10 + 40) * 3])

    def test_unqualified_dealer_pushes_the_seats(self):
        rules = Rules()
        seats = Seats(2)
        seats.hands = [cards('9S 9H'), cards('2S 3H')]
        board = cards('KD 5C 8S 7C QD')
        seats.act(board[:3], rules)
        seats.settle(board, evaluate(cards('AS 4H') + board), 10, rules)
        self.assertEqual(seats.delta, [0, -10])                       # the fold still lost its Ante
        self.assertEqual(seats.won, [False, False])

    def test_silent_refill(self):
        rules = Rules()
        seats = Seats(1)
        seats.chips = [30]
        seats.hands = [cards('2S 3H')]
        board = cards('KD 5C 8S 7C QD')
        seats.act(board[:3], rules)
        seats.settle(board, evaluate(cards('AS 4H') + board), 10, rules)
        self.assertEqual(seats.chips, [START - 10])

    def test_stack_height(self):
        s = Seats(1)
        for chips, h in ((0, 0), (199, 0), (200, 1), (1000, 5), (1399, 6), (5000, 6)):
            s.chips = [chips]
            self.assertEqual(s.stack_height(0), h, chips)


if __name__ == '__main__':
    unittest.main()
