import random
import unittest

import tests.context  # noqa: F401
from cards import (card_name, card_from_name, card_points, hand_value, Shoe, RANKS, SUITS)


def h(*names):
    return [card_from_name(n) for n in names]


class CardNames(unittest.TestCase):
    def test_names_match_asset_naming(self):
        self.assertEqual(card_name(0), 'AS')
        self.assertEqual(card_name(9 + 13), 'TH')
        self.assertEqual(card_name(6 + 39), '7C')
        self.assertEqual(card_name(51), 'KC')

    def test_round_trip_all_52(self):
        names = set()
        for c in range(52):
            self.assertEqual(card_from_name(card_name(c)), c)
            names.add(card_name(c))
        self.assertEqual(len(names), 52)
        for r in RANKS:
            for s in SUITS:
                self.assertIn(r + s, names)

    def test_points(self):
        self.assertEqual(card_points(card_from_name('AS')), 1)
        self.assertEqual(card_points(card_from_name('9H')), 9)
        for r in 'TJQK':
            self.assertEqual(card_points(card_from_name(r + 'D')), 10)


class HandValue(unittest.TestCase):
    def check(self, names, total, soft):
        self.assertEqual(hand_value(h(*names)), (total, soft), names)

    def test_no_aces(self):
        self.check(['TS', '7H'], 17, False)
        self.check(['KS', 'QH', '2C'], 22, False)

    def test_soft_hands(self):
        self.check(['AS', '6H'], 17, True)
        self.check(['AS', 'KH'], 21, True)
        self.check(['AS', 'AH'], 12, True)
        self.check(['AS', 'AH', '9C'], 21, True)
        self.check(['AS', '2H', '3C'], 16, True)

    def test_ace_demoted_to_one(self):
        self.check(['AS', '6H', 'TC'], 17, False)
        self.check(['AS', 'AH', 'AD', '8C'], 21, True)   # 11+1+1+8
        self.check(['AS', 'AH', 'TC', 'TD'], 22, False)
        self.check(['AS', 'KH', '5C'], 16, False)

    def test_four_aces(self):
        self.check(['AS', 'AH', 'AD', 'AC'], 14, True)

    def test_empty(self):
        self.assertEqual(hand_value([]), (0, False))


class ShoeTests(unittest.TestCase):
    def test_contents(self):
        for decks in (1, 2, 6):
            s = Shoe(decks, random.Random(1))
            self.assertEqual(s.remaining(), 52 * decks)
            counts = [0] * 52
            for c in s.cards:
                counts[c] += 1
            self.assertEqual(counts, [decks] * 52)

    def test_seed_is_deterministic(self):
        a = Shoe(6, random.Random(7)).cards
        b = Shoe(6, random.Random(7)).cards
        c = Shoe(6, random.Random(8)).cards
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    def test_shuffle_actually_mixes(self):
        s = Shoe(1, random.Random(3))
        self.assertNotEqual(list(s.cards), list(range(52)))

    def test_first_card_roughly_uniform(self):
        rng = random.Random(42)
        counts = [0] * 52
        n = 26000
        for _ in range(n):
            counts[Shoe(1, rng).cards[0]] += 1
        for k in counts:   # expected 500 each
            self.assertTrue(380 < k < 620, counts)

    def test_draw_and_penetration(self):
        s = Shoe(1, random.Random(1), penetration=0.5)
        for _ in range(25):
            s.draw()
        self.assertFalse(s.needs_shuffle())
        s.draw()
        self.assertTrue(s.needs_shuffle())
        s.shuffle()
        self.assertEqual(s.remaining(), 52)
        self.assertFalse(s.needs_shuffle())

    def test_draw_from_empty_reshuffles(self):
        s = Shoe(1, random.Random(1))
        for _ in range(52):
            s.draw()
        s.draw()
        self.assertEqual(s.remaining(), 51)

    def test_stacked(self):
        s = Shoe(1, random.Random(1), stacked=h('AS', 'KD'))
        self.assertEqual(card_name(s.draw()), 'AS')
        self.assertEqual(card_name(s.draw()), 'KD')
        with self.assertRaises(IndexError):
            s.draw()


if __name__ == '__main__':
    unittest.main()
