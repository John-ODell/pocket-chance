import random
import unittest

import tests.context  # noqa: F401
from cards import card_from_name, Shoe
from bankroll import Bankroll
from poker import evaluate5
from stud_rules import (Rules, Round, qualifies, advice, describe, RAISE_PAY,
                        FOLD, NOQUALIFY, WIN, LOSE, PUSH, DECISION, DONE)
from stud_table import StudTable, BETTING, DECIDING, RESULT, BROKE, MIN_ANTE, MAX_ANTE


def h(*names):
    return [card_from_name(n) for n in names]


def interleave(player, dealer):
    """Deal order is player, dealer, player, dealer ... so build the stacked shoe that way."""
    out = []
    for p, d in zip(player, dealer):
        out += [p, d]
    return out


def rnd(player, dealer, ante=10, rules=None):
    shoe = Shoe(1, random.Random(0), stacked=interleave(h(*player.split()), h(*dealer.split())))
    return Round(shoe, rules or Rules(), ante).deal()


class Qualify(unittest.TestCase):
    def v(self, s):
        return evaluate5(h(*s.split()))

    def test_boundary(self):
        self.assertTrue(qualifies(self.v('AS KD 4C 3H 2S')))        # lowest qualifier
        self.assertFalse(qualifies(self.v('AS QD JC TH 9S')))       # highest non-qualifier
        self.assertTrue(qualifies(self.v('2S 2D 4C 3H 7S')))
        self.assertFalse(qualifies(self.v('KS QD JC TH 8S')))

    def test_rules_parameter(self):
        self.assertTrue(qualifies(self.v('AS QD 4C 3H 2S'), Rules(qualify_rank=12)))
        self.assertFalse(qualifies(self.v('AS QD 4C 3H 2S'), Rules()))


class Advice(unittest.TestCase):
    def adv(self, player, up):
        p = h(*player.split())
        return advice(p, evaluate5(p), card_from_name(up))

    def test_pairs_and_below_ak(self):
        self.assertTrue(self.adv('9S 9D 4C 3H 2S', 'KH'))
        self.assertFalse(self.adv('AS QD 4C 3H 2S', '2H'))

    def test_ace_king_rules(self):
        self.assertTrue(self.adv('AS KD 4C 3H 2S', '4H'))      # up-card 2-Q matches one of ours
        self.assertFalse(self.adv('AS KD 4C 3H 2S', '9H'))     # no match, no queen
        self.assertTrue(self.adv('AS KD QC 3H 2S', 'KH'))      # up-card A/K and we hold a queen
        self.assertTrue(self.adv('AS KD JC 3H 2S', 'AH'))      # ... or a jack
        self.assertFalse(self.adv('AS KD TC 3H 2S', 'AH'))
        self.assertTrue(self.adv('AS KD QC 8H 2S', '5H'))      # no match, queen, up-card below our 4th card (8)
        self.assertFalse(self.adv('AS KD QC 8H 2S', '9H'))     # up-card above the 4th card


class Describe(unittest.TestCase):
    def test_names(self):
        d = lambda s: describe(evaluate5(h(*s.split())))
        self.assertEqual(d('AS KD 4C 3H 2S'), 'ace-king')
        self.assertEqual(d('QS JD 4C 3H 2S'), 'queen high')
        self.assertEqual(d('9S 9D 4C 3H 2S'), 'pair of 9s')
        self.assertEqual(d('AS AD 4C 3H 2S'), 'pair of aces')
        self.assertEqual(d('9S 9D 9C 3H 2S'), 'three 9s')
        self.assertEqual(d('9S 9D 9C 9H 2S'), 'four 9s')
        self.assertEqual(d('9S 9D 4C 4H 2S'), 'two pair')
        self.assertEqual(d('AS KS QS JS TS'), 'royal flush')


class RoundFlow(unittest.TestCase):
    def test_deal(self):
        r = rnd('9S 9D 4C 3H 2S', 'KH 7D 5C 3D 2D')
        self.assertEqual((len(r.player), len(r.dealer), r.state), (5, 5, DECISION))
        self.assertEqual(r.up_card(), card_from_name('KH'))

    def test_fold(self):
        r = rnd('9S 9D 4C 3H 2S', 'KH 7D 5C 3D 2D').fold()
        self.assertEqual((r.state, r.outcome, r.net, r.raise_bet), (DONE, FOLD, -10, 0))
        with self.assertRaises(ValueError):
            r.raise_()

    def test_dealer_does_not_qualify(self):
        r = rnd('9S 9D 4C 3H 2S', 'KH 7D 5C 3D 2D').raise_()
        self.assertEqual((r.outcome, r.net, r.raise_bet), (NOQUALIFY, 10, 20))
        self.assertFalse(r.dealer_qualifies())
        # even a losing player hand is paid the ante when the dealer does not qualify
        r = rnd('QS JD 4C 3H 2S', 'KH 7D 5C 3D 2D').raise_()
        self.assertEqual((r.outcome, r.net), (NOQUALIFY, 10))

    def test_win_pays_by_table(self):
        cases = [('9S 9D 4C 3H 2S', 'AH KD 5C 3D 2D', 10 + 20 * 1),          # pair v A-K
                 ('9S 9D 4C 4H 2S', 'AH KD 5C 3D 2D', 10 + 20 * 2),          # two pair
                 ('9S 9D 9C 3H 2S', 'AH KD 5C 3D 2D', 10 + 20 * 3),
                 ('9S 8D 7C 6H 5S', 'AH KD 5C 3D 2D', 10 + 20 * 4),
                 ('9S 2S 7S 6S KS', 'AH KD 5C 3D 2D', 10 + 20 * 5),
                 ('9S 9D 9C 3H 3S', 'AH KD 5C 3D 2D', 10 + 20 * 7),
                 ('9S 9D 9C 9H 3S', 'AH KD 5C 3D 2D', 10 + 20 * 20),
                 ('9S 8S 7S 6S 5S', 'AH KD 5C 3D 2D', 10 + 20 * 50),
                 ('AS KS QS JS TS', 'AH KD 5C 3D 2D', 10 + 20 * 100)]
        for p, d, net in cases:
            r = rnd(p, d).raise_()
            self.assertEqual((r.outcome, r.net), (WIN, net), p)

    def test_ace_king_beats_ace_king_by_kicker_and_ties_push(self):
        r = rnd('AS KD 9C 3H 2S', 'AH KC 8D 4D 2D').raise_()
        self.assertEqual((r.outcome, r.net), (WIN, 30))
        r = rnd('AS KD 9C 3H 2S', 'AH KC 9D 3D 2D').raise_()
        self.assertEqual((r.outcome, r.net), (PUSH, 0))

    def test_lose(self):
        r = rnd('9S 9D 4C 3H 2S', 'KH KD 5C 3D 2D').raise_()
        self.assertEqual((r.outcome, r.net, r.stake()), (LOSE, -30, 30))

    def test_raise_multiplier_parameter(self):
        r = rnd('9S 9D 4C 3H 2S', 'KH KD 5C 3D 2D', rules=Rules(raise_mult=1)).raise_()
        self.assertEqual(r.net, -20)


class TableFlow(unittest.TestCase):
    def table(self, balance=1000):
        return StudTable(random.Random(3), Bankroll(balance))

    def test_ante_limits(self):
        t = self.table()
        self.assertEqual(t.adjust_ante(1000), MAX_ANTE)
        self.assertEqual(t.adjust_ante(-1000), MIN_ANTE)
        t = self.table(balance=200)
        self.assertEqual(t.max_ante(), 65)                 # 200 // 3 = 66 -> 65
        self.assertEqual(t.adjust_ante(1000), 65)
        t = self.table(balance=14)
        self.assertEqual(t.state, BROKE)                   # cannot cover ante + raise
        self.assertFalse(self.table(balance=15).is_broke())

    def test_shared_bet_pulled_into_range(self):
        b = Bankroll(1000)
        b.bet = 500
        t = StudTable(random.Random(1), b)
        self.assertEqual(b.bet, MAX_ANTE)

    def test_hand_flow_and_stakes(self):
        t = self.table()
        t.adjust_ante(5)                                   # 10
        self.assertEqual(t.stakes(), (1000, 10, 0))
        t.deal()
        self.assertEqual(t.state, DECIDING)
        self.assertEqual(t.stakes(), (990, 10, 0))
        with self.assertRaises(ValueError):
            t.adjust_ante(5)
        t.raise_()
        self.assertEqual(t.state, RESULT)
        r = t.round
        self.assertEqual(t.bankroll.balance, 1000 + r.net)
        self.assertEqual(t.stakes(), (1000 + r.net, 10, 20))
        t.next_hand()
        self.assertEqual((t.state, t.bankroll.bet), (BETTING, 10))

    def test_fold_flow(self):
        t = self.table()
        t.deal()
        t.fold()
        self.assertEqual((t.state, t.bankroll.balance), (RESULT, 995))
        self.assertEqual(t.stakes(), (995, 5, 0))

    def test_many_hands_balance_consistent(self):
        t = self.table()
        bal = 1000
        rng = random.Random(8)
        for _ in range(500):
            if t.state == BROKE:
                t.refill()
                bal = 1000
            t.deal()
            if rng.random() < 0.5:
                t.raise_()
            else:
                t.fold()
            bal += t.round.net
            self.assertEqual(t.bankroll.balance, bal)
            self.assertEqual(sorted(t.round.player + t.round.dealer), sorted(set(t.round.player + t.round.dealer)))
            t.next_hand()

    def test_deck_reshuffled_every_hand(self):
        t = self.table()
        t.deal()
        t.fold()
        t.next_hand()
        t.deal()
        self.assertEqual(t.shoe.remaining(), 52 - 10 - 5 * t.seats.count)   # fresh deck minus the hand's cards


if __name__ == '__main__':
    unittest.main()
