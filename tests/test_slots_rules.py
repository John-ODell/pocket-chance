import random
import unittest

import tests.context  # noqa: F401
from slots_rules import (strip, Paytable, Reels, exact_stats, SYMBOLS,
                         CHERRY, LEMON, ORANGE, BELL, BAR, SEVEN, DIAMOND, STAR)

COUNTS = {CHERRY: 3, LEMON: 7, ORANGE: 6, BELL: 5, BAR: 4, SEVEN: 3, DIAMOND: 3, STAR: 1}
THREE = {STAR: 1000, DIAMOND: 200, SEVEN: 100, BAR: 40, BELL: 20, ORANGE: 14, LEMON: 10, CHERRY: 8}
PAY = Paytable(three=THREE, cherries={2: 3, 1: 1})


class Strip(unittest.TestCase):
    def test_counts_preserved(self):
        s = strip(COUNTS)
        self.assertEqual(len(s), 32)
        for sym, n in COUNTS.items():
            self.assertEqual(s.count(sym), n, SYMBOLS[sym])

    def test_common_symbols_are_spread(self):
        s = strip(COUNTS)
        for i in range(len(s)):
            if s[i] == LEMON:
                self.assertNotEqual(s[(i + 1) % len(s)], LEMON)   # no two lemons touching

    def test_single_symbol_strip(self):
        self.assertEqual(strip({BAR: 4}), [BAR] * 4)


class PaytableTests(unittest.TestCase):
    def test_three_of_a_kind(self):
        self.assertEqual(PAY.evaluate([STAR, STAR, STAR], 5), (5000, 'three star'))
        self.assertEqual(PAY.evaluate([CHERRY, CHERRY, CHERRY], 10), (80, 'three cherry'))

    def test_cherries(self):
        self.assertEqual(PAY.evaluate([CHERRY, CHERRY, BAR], 10), (30, '2 cherries'))
        self.assertEqual(PAY.evaluate([BAR, CHERRY, LEMON], 10), (10, '1 cherry'))
        self.assertEqual(PAY.evaluate([CHERRY, BAR, CHERRY], 10), (30, '2 cherries'))

    def test_nothing(self):
        self.assertEqual(PAY.evaluate([BAR, LEMON, SEVEN], 10), (0, None))
        self.assertEqual(Paytable({STAR: 10}).evaluate([BAR, BAR, BAR], 1), (0, None))

    def test_any_fruit(self):
        p = Paytable(THREE, {}, ({BAR, SEVEN, DIAMOND}, 10))
        self.assertEqual(p.evaluate([BAR, SEVEN, DIAMOND], 2)[0], 20)
        self.assertEqual(p.evaluate([BAR, BAR, BAR], 2)[0], 80)      # three of a kind wins over any-bar

    def test_top_prize(self):
        self.assertEqual(PAY.top_prize(), (STAR, 1000))


class ReelsTests(unittest.TestCase):
    def test_spin_and_line(self):
        r = Reels([strip(COUNTS)] * 3, PAY, random.Random(1))
        win, label = r.spin(5)
        line = r.line()
        self.assertEqual(len(line), 3)
        self.assertEqual((win, label), PAY.evaluate(line, 5))
        for i in range(3):
            self.assertEqual(r.symbol_at(i, 0), line[i])
            self.assertEqual(r.symbol_at(i, 32), line[i])      # wraps

    def test_rtp_over_many_spins_matches_exact(self):
        strips = [strip(COUNTS)] * 3
        exact = exact_stats(strips, PAY)
        r = Reels(strips, PAY, random.Random(7))
        n = 200000
        ret = 0
        for _ in range(n):
            ret += r.spin(1)[0]
        self.assertAlmostEqual(ret / float(n), exact['rtp'], delta=0.02)

    def test_exact_stats_recommended_table(self):
        st = exact_stats([strip(COUNTS)] * 3, PAY)
        self.assertEqual(st['combos'], 32768)
        self.assertAlmostEqual(st['rtp'], 0.9384, places=3)          # DR-018 option A
        self.assertAlmostEqual(1 / st['hit'], 3.6, places=1)
        self.assertAlmostEqual(st['top'], 1 / 32768.0)
        self.assertAlmostEqual(st['sd'], 8.9, places=1)


if __name__ == '__main__':
    unittest.main()
