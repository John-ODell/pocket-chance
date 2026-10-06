"""Baccarat rules (DR-051), pays (DR-059), table flow (DR-053, DR-054, DR-056) and history (DR-060)."""
import random
import unittest

import tests.context  # noqa: F401
from bankroll import Bankroll
from cards import Shoe, card_from_name
from baccarat_rules import (Coup, PLAYER, BANKER, TIE, points, total, banker_draws, banker_pay, settle,
                            PENETRATION, DECKS)
from baccarat_table import BaccaratTable, BETTING, RESULT, BROKE, HISTORY


def stacked(names):
    cards = [card_from_name(n) for n in names.split()]
    rest = [c for c in range(52) if c not in cards]
    return Shoe(1, random.Random(0), stacked=cards + rest)


class Rules(unittest.TestCase):
    def test_points_and_totals(self):
        self.assertEqual([points(card_from_name(n)) for n in 'AS 2H 9D TS JC QH KD'.split()], [1, 2, 9, 0, 0, 0, 0])
        self.assertEqual(total([card_from_name('9S'), card_from_name('7H')]), 6)       # 16 -> 6
        self.assertEqual(total([card_from_name('KS'), card_from_name('TH')]), 0)

    def test_banker_tableau(self):
        # Player stood: Banker draws on 0-5
        for b in range(6):
            self.assertTrue(banker_draws(b, None), b)
        self.assertFalse(banker_draws(6, None))
        self.assertFalse(banker_draws(7, None))
        # Player drew a third card of value v
        for b in (0, 1, 2):
            self.assertTrue(all(banker_draws(b, v) for v in range(10)), b)
        self.assertEqual([banker_draws(3, v) for v in range(10)], [True] * 8 + [False, True])
        self.assertEqual([banker_draws(4, v) for v in range(10)], [False, False] + [True] * 6 + [False, False])
        self.assertEqual([banker_draws(5, v) for v in range(10)], [False] * 4 + [True] * 4 + [False, False])
        self.assertEqual([banker_draws(6, v) for v in range(10)], [False] * 6 + [True, True, False, False])
        self.assertFalse(any(banker_draws(7, v) for v in range(10)))

    def test_natural_ends_the_coup(self):
        c = Coup(stacked('9S KH 5D 2C 7S'))                  # Player 9+5 = 4? no: P 9,5 -> 4; make a natural
        # order P, B, P, B: Player 9S 5D = 14 -> 4, Banker KH 2C = 2: Player draws
        self.assertEqual(c.order, [PLAYER, BANKER, PLAYER, BANKER, PLAYER, BANKER])
        c = Coup(stacked('9S KH TD 2C'))                     # Player 9 + 0 = 9 natural
        self.assertTrue(c.natural)
        self.assertEqual(len(c.order), 4)
        self.assertEqual(c.totals(), (9, 2))
        self.assertEqual(c.winner, PLAYER)

    def test_third_card_cases(self):
        # Player 6 stands, Banker 5 draws (Player stood rule)
        c = Coup(stacked('4S 3H 2D 2C 8S'))                  # P 4+2 = 6, B 3+2 = 5 -> Banker draws 8S -> 3
        self.assertEqual(c.order, [PLAYER, BANKER, PLAYER, BANKER, BANKER])
        self.assertEqual(c.totals(), (6, 3))
        self.assertEqual(c.winner, PLAYER)
        # Player 3 draws an 8; Banker 3 stands against an 8
        c = Coup(stacked('AS 2H 2D AC 8S'))                  # P 1+2 = 3 draws 8 -> 1; B 2+1 = 3, v = 8: stands
        self.assertEqual(c.order, [PLAYER, BANKER, PLAYER, BANKER, PLAYER])
        self.assertEqual(c.totals(), (1, 3))
        self.assertEqual(c.winner, BANKER)
        # Player 7 stands, Banker 7 stands: tie
        c = Coup(stacked('4S 3H 3D 4C'))
        self.assertEqual(len(c.order), 4)
        self.assertEqual(c.winner, TIE)
        self.assertFalse(c.natural)

    def test_shown_counts_cards_in_deal_order(self):
        c = Coup(stacked('4S 3H 2D 2C 8S'))
        self.assertEqual(c.shown(0), ([], []))
        p, b = c.shown(3)
        self.assertEqual((len(p), len(b)), (2, 1))
        p, b = c.shown(5)
        self.assertEqual((len(p), len(b)), (2, 3))

    def test_pays(self):
        self.assertEqual([banker_pay(s) for s in (5, 10, 15, 20, 25, 50, 100)], [4, 9, 14, 19, 23, 47, 95])
        self.assertEqual(settle(PLAYER, 20, PLAYER), 20)
        self.assertEqual(settle(PLAYER, 20, BANKER), -20)
        self.assertEqual(settle(PLAYER, 20, TIE), 0)
        self.assertEqual(settle(BANKER, 20, BANKER), 19)
        self.assertEqual(settle(BANKER, 5, BANKER), 4)
        self.assertEqual(settle(BANKER, 20, PLAYER), -20)
        self.assertEqual(settle(BANKER, 20, TIE), 0)
        self.assertEqual(settle(TIE, 20, TIE), 160)
        self.assertEqual(settle(TIE, 20, PLAYER), -20)

    def test_edge_sanity(self):
        """A long run of coups lands near the exact edges (Banker 1.06%, Player 1.24%, Tie 14.4%)."""
        shoe = Shoe(DECKS, random.Random(5), penetration=PENETRATION)
        n = 60000
        net = [0, 0, 0]
        for _ in range(n):
            if shoe.needs_shuffle():
                shoe.shuffle()
            w = Coup(shoe).winner
            for side in (PLAYER, BANKER, TIE):
                net[side] += settle(side, 20, w)
        edge = [-100.0 * net[s] / (20 * n) for s in (PLAYER, BANKER, TIE)]
        self.assertAlmostEqual(edge[PLAYER], 1.24, delta=1.0)
        self.assertAlmostEqual(edge[BANKER], 1.06, delta=1.0)
        self.assertAlmostEqual(edge[TIE], 14.36, delta=3.0)


class Table(unittest.TestCase):
    def test_stake_limits(self):
        t = BaccaratTable(random.Random(1), Bankroll(1000), seats=0)
        self.assertEqual(t.bankroll.bet, 5)
        self.assertEqual(t.adjust_stake(1000), 100)
        self.assertEqual(t.adjust_stake(-1000), 5)
        t = BaccaratTable(random.Random(1), Bankroll(37), seats=0)
        self.assertEqual(t.adjust_stake(1000), 35)                   # capped at the balance, whole steps
        t = BaccaratTable(random.Random(1), Bankroll(4), seats=0)
        self.assertEqual(t.state, BROKE)
        t.refill()
        self.assertEqual((t.state, t.bankroll.balance, t.bankroll.bet), (BETTING, 1000, 5))

    def test_select_side(self):
        t = BaccaratTable(random.Random(1), Bankroll(1000), seats=0)
        self.assertEqual(t.side, PLAYER)
        self.assertEqual(t.select(1), TIE)
        self.assertEqual(t.select(1), BANKER)
        self.assertEqual(t.select(1), BANKER)
        self.assertEqual(t.select(-1), TIE)
        self.assertEqual(t.select(-1), PLAYER)
        self.assertEqual(t.select(-1), PLAYER)

    def test_coup_settles_and_history(self):
        t = BaccaratTable(random.Random(1), Bankroll(1000), seats=0)
        t.adjust_stake(15)                                          # stake 20
        t.select(1)
        t.select(1)                                                 # Banker
        t.shoe = stacked('9S KH TD 2C')                             # Player natural 9: Banker loses
        t.deal()
        self.assertEqual((t.state, t.net, t.bankroll.balance), (RESULT, -20, 980))
        self.assertEqual(t.history, [PLAYER])
        self.assertEqual(t.stakes(), (980, 20))
        self.assertEqual(t.stakes(revealing=True), (980, 20))      # stake off, result not yet in: 1000 - 20
        with self.assertRaises(ValueError):
            t.deal()
        t.next_coup()
        self.assertEqual(t.state, BETTING)
        t.shoe = stacked('4S 3H 3D 4C')                             # tie: Banker bet pushes
        t.deal()
        self.assertEqual((t.net, t.bankroll.balance), (0, 980))
        self.assertEqual(t.stakes(revealing=True), (960, 20))
        self.assertEqual(t.history, [PLAYER, TIE])
        t.next_coup()
        t.select(-1)                                                # Tie
        t.shoe = stacked('4S 3H 3D 4C')
        t.deal()
        self.assertEqual((t.net, t.bankroll.balance), (160, 1140))
        self.assertEqual(t.history, [PLAYER, TIE, TIE])

    def test_history_keeps_twelve(self):
        t = BaccaratTable(random.Random(3), Bankroll(100000), seats=0)
        for _ in range(HISTORY + 5):
            t.deal()
            t.next_coup()
        self.assertEqual(len(t.history), HISTORY)

    def test_shoe_reshuffles_at_the_cut_card(self):
        t = BaccaratTable(random.Random(3), Bankroll(100000), seats=0)
        self.assertEqual(t.shoe.remaining(), 52 * DECKS)
        shuffles = 0
        for _ in range(120):
            t.deal()
            shuffles += t.shuffled
            self.assertLessEqual(t.shoe.pos, 52 * DECKS)
            t.next_coup()
        self.assertGreaterEqual(shuffles, 1)                        # 120 coups use more than 416 cards

    def test_broke_after_losing_everything(self):
        t = BaccaratTable(random.Random(1), Bankroll(5), seats=0)
        t.shoe = stacked('9S KH TD 2C')                             # Player wins
        t.select(1)
        t.select(1)                                                 # Banker: lose 5
        t.deal()
        self.assertEqual(t.bankroll.balance, 0)
        t.next_coup()
        self.assertEqual(t.state, BROKE)


if __name__ == '__main__':
    unittest.main()
