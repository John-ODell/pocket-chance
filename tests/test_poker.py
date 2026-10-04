import random
import unittest

import tests.context  # noqa: F401
from cards import card_from_name
from poker import (evaluate, evaluate5, name, compare, rank_value,
                   HIGH_CARD, PAIR, TWO_PAIR, TRIPS, STRAIGHT, FLUSH, FULL_HOUSE, QUADS,
                   STRAIGHT_FLUSH, ROYAL_FLUSH)


def h(s):
    return [card_from_name(n) for n in s.split()]


class Categories(unittest.TestCase):
    def cat(self, s):
        return evaluate(h(s))[0]

    def test_each_category(self):
        self.assertEqual(self.cat('AS KD 9C 5H 2S'), HIGH_CARD)
        self.assertEqual(self.cat('AS AD 9C 5H 2S'), PAIR)
        self.assertEqual(self.cat('AS AD 9C 9H 2S'), TWO_PAIR)
        self.assertEqual(self.cat('AS AD AC 9H 2S'), TRIPS)
        self.assertEqual(self.cat('9S 8D 7C 6H 5S'), STRAIGHT)
        self.assertEqual(self.cat('AS 2S 3S 4S 5S'), STRAIGHT_FLUSH)
        self.assertEqual(self.cat('AS 2D 3S 4S 5S'), STRAIGHT)          # wheel
        self.assertEqual(self.cat('AS KS 9S 5S 2S'), FLUSH)
        self.assertEqual(self.cat('AS AD AC 9H 9S'), FULL_HOUSE)
        self.assertEqual(self.cat('AS AD AC AH 9S'), QUADS)
        self.assertEqual(self.cat('9S 8S 7S 6S 5S'), STRAIGHT_FLUSH)
        self.assertEqual(self.cat('AS KS QS JS TS'), ROYAL_FLUSH)

    def test_names(self):
        self.assertEqual(name(evaluate(h('AS AD 9C 9H 2S'))), 'two pair')
        self.assertEqual(name(evaluate(h('AS KS QS JS TS'))), 'royal flush')

    def test_not_a_straight_around_the_corner(self):
        self.assertEqual(self.cat('QS KD AC 2H 3S'), HIGH_CARD)

    def test_ace_high(self):
        self.assertEqual(rank_value(card_from_name('AS')), 14)
        self.assertEqual(rank_value(card_from_name('2S')), 2)
        self.assertEqual(rank_value(card_from_name('KS')), 13)


class Ordering(unittest.TestCase):
    def beats(self, a, b):
        self.assertEqual(compare(evaluate(h(a)), evaluate(h(b))), 1, '%s should beat %s' % (a, b))
        self.assertEqual(compare(evaluate(h(b)), evaluate(h(a))), -1)

    def ties(self, a, b):
        self.assertEqual(compare(evaluate(h(a)), evaluate(h(b))), 0)

    def test_category_order(self):
        order = ['AS KD 9C 5H 2S', '2S 2D 9C 5H 3S', '2S 2D 3C 3H 4S', '2S 2D 2C 5H 3S', 'AS 2D 3S 4S 5S',
                 '2S 7S 9S JS KS', '2S 2D 2C 3H 3S', '2S 2D 2C 2H 3S', 'AS 2S 3S 4S 5S', 'AS KS QS JS TS']
        for i in range(len(order) - 1):
            self.beats(order[i + 1], order[i])

    def test_kickers(self):
        self.beats('AS KD 9C 5H 3S', 'AS KD 9C 5H 2S')
        self.beats('AS AD 9C 5H 2S', 'KS KD 9C 5H 2S')
        self.beats('AS AD 9C 5H 2S', 'AC AH 8C 5D 2D')
        self.beats('AS AD 9C 9H 2S', 'AC AH 8C 8D KD')          # higher second pair
        self.beats('AS AD 9C 9H 3S', 'AC AH 9D 9S 2D')          # kicker on two pair
        self.beats('3S 3D 3C 2H 4S', '2S 2D 2C AH KS')          # trips rank over kickers
        self.beats('6S 5D 4C 3H 2S', 'AS 2D 3S 4S 5S')          # 6-high beats the wheel
        self.beats('AS 2D 3S 4S 5S', 'KS KD 9C 5H 2S')          # straight beats a pair
        self.beats('AS KS 9S 5S 2S', 'AD KD 9D 5D 3D'[:0] + 'AD KD 9D 4D 3D')
        self.beats('3S 3D 3C 2H 2S', '2S 2D 2C AH AS')          # full house by trips rank
        self.beats('3S 3D 3C 3H 2S', '2S 2D 2C 2H AS')

    def test_ties(self):
        self.ties('AS KD 9C 5H 2S', 'AH KC 9D 5S 2C')
        self.ties('9S 8D 7C 6H 5S', '9D 8C 7H 6S 5D')
        self.ties('AS 2S 3S 4S 5S', 'AD 2D 3D 4D 5D')


class SevenCards(unittest.TestCase):
    def test_best_of_seven(self):
        v = evaluate(h('AS KS QS JS TS 2D 3C'))
        self.assertEqual(v[0], ROYAL_FLUSH)
        v = evaluate(h('2S 2D 3C 3H 4S 4D 9C'))
        self.assertEqual(v[0], TWO_PAIR)
        self.assertEqual(v[1:3], (4, 3))                      # the two best pairs
        v = evaluate(h('9S 8D 7C 6H 5S 4D KC'))
        self.assertEqual((v[0], v[1]), (STRAIGHT, 9))
        v = evaluate(h('AS AD 9C 9H 9S 2D 2C'))
        self.assertEqual((v[0], v[1], v[2]), (FULL_HOUSE, 9, 14))

    def test_six_cards_and_too_few(self):
        self.assertEqual(evaluate(h('AS AD 9C 9H 2S 2D'))[0], TWO_PAIR)
        with self.assertRaises(ValueError):
            evaluate(h('AS AD 9C 9H'))

    def test_sampled_frequencies_are_sane(self):
        # 5-card frequencies: pair 42.3%, two pair 4.75%, trips 2.11%, straight 0.39%, flush 0.20%
        rng = random.Random(3)
        n = 40000
        counts = [0] * 10
        deck = list(range(52))
        for _ in range(n):
            rng.shuffle(deck)
            counts[evaluate5(deck[:5])[0]] += 1
        self.assertAlmostEqual(counts[HIGH_CARD] / n, 0.5012, delta=0.01)
        self.assertAlmostEqual(counts[PAIR] / n, 0.4226, delta=0.01)
        self.assertAlmostEqual(counts[TWO_PAIR] / n, 0.0475, delta=0.005)
        self.assertAlmostEqual(counts[TRIPS] / n, 0.0211, delta=0.004)
        self.assertAlmostEqual(counts[STRAIGHT] / n, 0.0039, delta=0.002)
        self.assertAlmostEqual(counts[FLUSH] / n, 0.0020, delta=0.0015)


if __name__ == '__main__':
    unittest.main()
