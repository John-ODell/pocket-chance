import random
import unittest

import tests.context  # noqa: F401
from bankroll import Bankroll
from cards import card_from_name, Shoe
from poker import evaluate, PAIR, STRAIGHT, FLUSH, ROYAL_FLUSH
from holdem_rules import (Rules, Round, resolve, blind_win, preflop_raise, flop_raise, hidden_pair_or_better,
                          dealer_outs, river_raise, describe, PREFLOP, FLOP, RIVER, DONE, WIN, LOSE, PUSH, FOLD)
from holdem_seats import Seats, START
from holdem_table import HoldemTable, BETTING, RESULT, BROKE, MIN_ANTE, MAX_ANTE


def h(s):
    return [card_from_name(n) for n in s.split()]


def rnd(player, dealer, board, ante=10):
    shoe = Shoe(1, random.Random(0), stacked=h(player) + h(dealer) + h(board))
    return Round(shoe, Rules(), ante).deal()


class Payouts(unittest.TestCase):
    def test_blind_table(self):
        r = Rules()
        self.assertEqual(blind_win(10, STRAIGHT, r), 10)
        self.assertEqual(blind_win(10, FLUSH, r), 15)
        self.assertEqual(blind_win(10, 6, r), 30)             # full house 3:1
        self.assertEqual(blind_win(10, 7, r), 100)            # quads 10:1
        self.assertEqual(blind_win(10, 8, r), 500)            # straight flush 50:1
        self.assertEqual(blind_win(10, ROYAL_FLUSH, r), 5000)
        self.assertEqual(blind_win(10, PAIR, r), 0)
        self.assertEqual(blind_win(5, FLUSH, r), 7)           # rounds down

    def test_resolve(self):
        r = Rules()
        pair = evaluate(h('9S 9D 4C 3H 2S KD 7C'))
        twop = evaluate(h('9S 9D 4C 4H 2S KD 7C'))
        high = evaluate(h('AS QD 4C 3H 2S KD 7C'))
        flush = evaluate(h('9S 2S 4S 3S KS QD 7C'))
        self.assertEqual(resolve(twop, pair, 10, 40, r), (WIN, 40 + 10, True))             # dealer qualified, no blind
        self.assertEqual(resolve(pair, high, 10, 40, r), (WIN, 40, False))                  # dealer unqualified: ante pushes
        self.assertEqual(resolve(flush, pair, 10, 10, r), (WIN, 10 + 10 + 15, True))        # blind pays 3:2
        self.assertEqual(resolve(pair, twop, 10, 40, r), (LOSE, -(40 + 10 + 10), True))
        self.assertEqual(resolve(high, pair, 10, 20, r), (LOSE, -(20 + 10 + 10), True))
        self.assertEqual(resolve(pair, pair, 10, 40, r), (PUSH, 0, True))

    def test_lose_to_unqualified_dealer_keeps_ante(self):
        high_a = evaluate(h('AS QD 4C 3H 2S KD 7C'))
        high_k = evaluate(h('KS QD 4C 3H 2S JD 7C'))
        self.assertEqual(resolve(high_k, high_a, 10, 40, Rules()), (LOSE, -(40 + 10), False))


class Strategy(unittest.TestCase):
    def test_preflop(self):
        yes = ['3S 3D', 'AS 2D', 'KS 2S', 'KS 5D', 'QS 6S', 'QS 8D', 'JS 8S', 'JS TD']
        no = ['2S 2D', 'KS 4D', 'QS 5S', 'QS 7D', 'JS 7S', 'JS 9D', 'TS 9S', '7S 2D']
        for s in yes:
            self.assertTrue(preflop_raise(h(s)), s)
        for s in no:
            self.assertFalse(preflop_raise(h(s)), s)

    def test_flop(self):
        self.assertTrue(flop_raise(h('9S 4D'), h('9H KC 2D')))          # hidden pair
        self.assertFalse(flop_raise(h('9S 4D'), h('KH KC 2D')))         # board pair only
        self.assertFalse(flop_raise(h('2S 2D'), h('KH 7C 9D')))         # pocket deuces
        self.assertTrue(flop_raise(h('TS 4S'), h('KS 7S 9D')))          # four to a flush with a hidden ten
        self.assertFalse(flop_raise(h('9S 4S'), h('KS 7S 2D')))         # four to a flush, no hidden ten+
        self.assertTrue(flop_raise(h('9S 4D'), h('9H 4C 2D')))          # two pair

    def test_hidden_pair_at_the_river(self):
        self.assertTrue(hidden_pair_or_better(h('9S 4D'), h('9H KC 2D 7S 3C')))
        self.assertFalse(hidden_pair_or_better(h('AS 4D'), h('9H 9C 2D 7S 3C')))    # board pair, ace kicker
        self.assertTrue(hidden_pair_or_better(h('AS 4D'), h('9H 9C 4C 7S 3C')))     # two pair using a hole card
        self.assertFalse(hidden_pair_or_better(h('AS QD'), h('9H 9C 4C 4S 3C')))    # board two pair only

    def test_dealer_outs_and_river_rule(self):
        # queen high on a dry board: any board pair (15) or any A/K (8) beats it: 23 outs; a made straight: few
        n = dealer_outs(h('QS JD'), h('9H 7C 4D 2S 3C'))
        self.assertEqual(n, 23)
        self.assertFalse(river_raise(h('QS JD'), h('9H 7C 4D 2S 3C'), n))
        # ace-queen high: only the 15 board pairs beat it (an ace gives the dealer a worse kicker)
        self.assertEqual(dealer_outs(h('AS QD'), h('9H 7C 4D 2S 3C')), 15)
        m = dealer_outs(h('8S 6D'), h('9H 7C 5D 2S 3C'))              # straight 5-9
        self.assertLess(m, 21)
        self.assertTrue(river_raise(h('8S 6D'), h('9H 7C 5D 2S 3C'), m))
        self.assertTrue(river_raise(h('9S 4D'), h('9H KC 2D 7S 3C')))   # hidden pair, no count needed
        self.assertFalse(river_raise(h('QS JD'), h('9H 7C 4D 2S 3C')))  # no count given: fold

    def test_describe(self):
        self.assertEqual(describe(evaluate(h('9S 9D 4C 3H 2S KD 7C'))), 'pair of 9s')
        self.assertEqual(describe(evaluate(h('AS QD 4C 3H 2S KD 7C'))), 'ace high')
        self.assertEqual(describe(evaluate(h('9S 2S 4S 3S KS QD 7C'))), 'flush')


class RoundFlow(unittest.TestCase):
    def test_phases_and_shown_board(self):
        r = rnd('9S 9D', 'KH 2C', '4C 3H 7D QS JC')
        self.assertEqual((r.state, r.shown_board()), (PREFLOP, []))
        r.check()
        self.assertEqual((r.state, len(r.shown_board())), (FLOP, 3))
        r.check()
        self.assertEqual((r.state, len(r.shown_board())), (RIVER, 5))
        with self.assertRaises(ValueError):
            r.check()

    def test_raises_by_phase(self):
        r = rnd('9S 9D', 'KH 2C', '4C 3H 7D QS JC')
        with self.assertRaises(ValueError):
            r.raise_(2)
        r.raise_(4)
        self.assertEqual((r.state, r.play_bet, r.outcome), (DONE, 40, WIN))
        self.assertEqual(r.net, 40 + 0)                       # dealer K high: unqualified, ante pushes
        self.assertFalse(r.qualified)
        r = rnd('9S 9D', 'KH 2C', '4C 3H 7D QS JC')
        r.check()
        with self.assertRaises(ValueError):
            r.raise_(4)
        r.raise_(2)
        self.assertEqual(r.play_bet, 20)
        r = rnd('9S 9D', 'KH 2C', '4C 3H 7D QS JC')
        r.check().check().raise_(1)
        self.assertEqual(r.play_bet, 10)

    def test_three_x_pre_flop(self):
        r = rnd('9S 9D', 'KH 2C', '4C 3H 7D QS JC')
        r.raise_(3)
        self.assertEqual(r.play_bet, 30)

    def test_fold(self):
        r = rnd('9S 4D', 'KH KC', '5C 3H 7D QS JC')
        with self.assertRaises(ValueError):
            r.fold()
        r.check().check().fold()
        self.assertEqual((r.outcome, r.net, r.state), (FOLD, -20, DONE))
        self.assertTrue(r.qualified)

    def test_blind_pays_on_a_won_flush(self):
        r = rnd('9S 2S', 'KH 2C', '4S 3S QS JC 7D')
        r.raise_(4)
        self.assertEqual(r.outcome, WIN)
        self.assertEqual(r.net, 40 + 0 + 15)                  # dealer unqualified: ante pushes, blind 3:2

    def test_outs(self):
        r = rnd('QS JD', 'KH 2C', '9H 7C 4D 2S 3C')
        r.check().check()
        self.assertEqual(r.outs(), 23)


class SeatsLogic(unittest.TestCase):
    def test_deal_and_decisions(self):
        shoe = Shoe(1, random.Random(4), penetration=0.0)
        shoe.shuffle()
        used = [shoe.draw() for _ in range(9)]
        s = Seats(4)
        s.deal(shoe)
        cards = used + [c for hd in s.hands for c in hd]
        self.assertEqual(len(set(cards)), 17)
        board = used[4:9]
        s.act_preflop(Rules())
        s.act_flop(board[:3])
        s.act_river(board)
        for i in range(4):
            self.assertIn(s.status(i), ('4x', '2x', '1x', 'fold'))
        dv = evaluate(used[2:4] + board)
        s.settle(board, dv, 10, Rules())
        self.assertTrue(all(d != 0 for d in s.delta))
        for i in range(4):
            if s.folded[i]:
                self.assertEqual(s.delta[i], -20)

    def test_refill_and_zero(self):
        s = Seats(1)
        s.chips = [10]
        s.hands = [h('2S 7D')]
        s.folded = [True]
        s.settle(h('9H KC 4D QS JC'), evaluate(h('AS AD 9H KC 4D QS JC')), 10, Rules())
        self.assertEqual(s.chips, [START - 20])
        self.assertEqual(Seats(0).count, 0)
        self.assertEqual(Seats(9).count, 4)


class TableFlow(unittest.TestCase):
    def table(self, balance=1000, **kw):
        return HoldemTable(random.Random(5), Bankroll(balance), **kw)

    def test_ante_limits(self):
        t = self.table()
        self.assertEqual(t.adjust_ante(1000), MAX_ANTE)
        self.assertEqual(t.adjust_ante(-1000), MIN_ANTE)
        self.assertEqual(self.table(balance=200).max_ante(), 30)         # 200 // 6 = 33 -> 30
        self.assertEqual(self.table(balance=29).state, BROKE)
        self.assertEqual(self.table(balance=30).state, BETTING)

    def test_flow_and_stakes_and_outs(self):
        t = self.table()
        t.adjust_ante(5)                                                  # 10
        t.deal()
        self.assertEqual((t.state, t.stakes()), (PREFLOP, (980, 10, 0)))
        t.check()
        self.assertEqual(t.state, FLOP)
        self.assertIsNone(t.outs)
        t.check()
        self.assertEqual(t.state, RIVER)
        self.assertIsNone(t.outs)                                         # the screen asks for the hint
        self.assertIsNotNone(t.compute_outs())
        self.assertTrue(0 <= t.outs <= 45)
        self.assertEqual(t.compute_outs(), t.outs)                        # computed once
        t.raise_(1)
        self.assertEqual(t.state, RESULT)
        r = t.round
        self.assertEqual(t.bankroll.balance, 1000 + r.net)
        self.assertEqual(t.stakes(), (1000 + r.net, 10, 10))
        self.assertTrue(all(d != 0 for d in t.seats.delta))
        t.next_hand()
        self.assertEqual(t.state, BETTING)

    def test_hint_off(self):
        t = self.table(hint=False)
        t.deal()
        t.check()
        t.check()
        self.assertIsNone(t.compute_outs())
        self.assertIsNone(t.outs)

    def test_seats_never_touch_the_player(self):
        a = HoldemTable(random.Random(11), Bankroll(1000), seats=4)
        b = HoldemTable(random.Random(11), Bankroll(1000), seats=0)
        for _ in range(40):
            a.deal()
            b.deal()
            self.assertEqual(a.round.player, b.round.player)
            self.assertEqual(a.round.board, b.round.board)
            a.raise_(4)
            b.raise_(4)
            self.assertEqual(a.round.net, b.round.net)
            a.next_hand()
            b.next_hand()
            if a.state != BETTING:
                a.refill(); b.refill()

    def test_balance_arithmetic_many_hands(self):
        t = self.table()
        rng = random.Random(8)
        bal = 1000
        for _ in range(200):
            if t.state == BROKE:
                t.refill()
                bal = 1000
            t.deal()
            path = rng.choice(['4', '3', 'c2', 'cc1', 'ccf'])
            if path == '4':
                t.raise_(4)
            elif path == '3':
                t.raise_(3)
            elif path == 'c2':
                t.check(); t.raise_(2)
            elif path == 'cc1':
                t.check(); t.check(); t.raise_(1)
            else:
                t.check(); t.check(); t.fold()
            bal += t.round.net
            self.assertEqual(t.bankroll.balance, bal)
            t.next_hand()


if __name__ == '__main__':
    unittest.main()
