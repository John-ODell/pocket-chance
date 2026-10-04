"""Caribbean (Casino Hold'em with a low/high call): rules, pays, multiplier and table flow."""
import random
import unittest

import tests.context  # noqa: F401
from bankroll import Bankroll
from cards import Shoe, card_from_name
from poker import evaluate, PAIR, FLUSH, ROYAL_FLUSH
from caribbean_rules import (Rules, Round, qualifies, resolve, advice, has_draw, LOW, HIGH,
                             WIN, LOSE, PUSH, FOLD, DECIDING, DONE)
from caribbean_table import CaribbeanTable, BETTING, RESULT, BROKE, MIN_ANTE


def cards(names):
    return [card_from_name(n) for n in names.split()]


def stacked(player, dealer, board):
    out = cards(player + ' ' + dealer + ' ' + board)
    out += [c for c in range(52) if c not in out]
    return Shoe(1, random.Random(0), stacked=out)


class RulesTests(unittest.TestCase):
    def test_qualifies_with_a_pair_of_fours(self):
        rules = Rules()
        self.assertFalse(qualifies(evaluate(cards('3S 3H 7D 9C KS')), rules))
        self.assertTrue(qualifies(evaluate(cards('4S 4H 7D 9C KS')), rules))
        self.assertFalse(qualifies(evaluate(cards('AS KH 7D 9C 2S')), rules))
        self.assertTrue(qualifies(evaluate(cards('2S 3S 4S 5S 9S')), rules))

    def test_resolve_pays(self):
        rules = Rules()
        dq = evaluate(cards('9S 9H 2D 5C KD 7H 3S'))                 # pair of 9s, qualifies
        flush = evaluate(cards('2S 6S 9S JS KS 4H 7D'))
        self.assertEqual(resolve(flush, dq, 10, 40, rules), (WIN, 10 * 2 + 40, True))
        royal = evaluate(cards('TS JS QS KS AS 2H 3D'))
        self.assertEqual(resolve(royal, dq, 10, 20, rules), (WIN, 1000 + 20, True))
        pair = evaluate(cards('8S 8H 2D 5C KD 7H 3S'))
        self.assertEqual(resolve(pair, dq, 10, 20, rules), (LOSE, -30, True))
        self.assertEqual(resolve(dq, dq, 10, 20, rules), (PUSH, 0, True))
        # multiplier on the call only
        self.assertEqual(resolve(flush, dq, 10, 40, rules, 3), (WIN, 20 + 120, True))
        # unqualified dealer: everything pushes, even against a royal (John's ruling)
        dn = evaluate(cards('3S 2H 7D 9C KD 5H 8S'))
        self.assertEqual(resolve(royal, dn, 10, 40, rules), (PUSH, 0, False))
        self.assertEqual(resolve(pair, dn, 10, 40, rules), (PUSH, 0, False))

    def test_draws(self):
        self.assertTrue(has_draw(cards('2S 9S'), cards('5S KS 7D')))          # four spades, two in hand
        self.assertFalse(has_draw(cards('2H 9D'), cards('5S KS 7S')))         # board flush draw only
        self.assertTrue(has_draw(cards('9S TH'), cards('JD QC 2S')))          # open-ended 9-T-J-Q
        self.assertTrue(has_draw(cards('9S JH'), cards('TD QC 2S')))          # inside draw
        self.assertTrue(has_draw(cards('AS 2H'), cards('3D 4C 9S')))          # wheel draw with the ace
        self.assertFalse(has_draw(cards('2S 7H'), cards('9D KC 4S')))

    def test_advice(self):
        self.assertEqual(advice(cards('9S 9H'), cards('2D 5C KS')), HIGH)      # pocket pair
        self.assertEqual(advice(cards('KS 4H'), cards('KD 5C 9S')), HIGH)      # pair using a hole card
        self.assertEqual(advice(cards('AS 4H'), cards('KD KC 9S')), LOW)       # board pair, ace high
        self.assertEqual(advice(cards('2S 3H'), cards('KD KC 9S')), LOW)       # board pair only: play low
        self.assertEqual(advice(cards('2S 9S'), cards('5S KS 7D')), LOW)       # flush draw
        self.assertEqual(advice(cards('AS 2H'), cards('5D 9C KS')), LOW)       # ace beats the table
        self.assertEqual(advice(cards('QS 2H'), cards('5D 9C KS')), None)      # nothing: fold
        self.assertEqual(advice(cards('2S 3H'), cards('5D 9C KS')), None)

    def test_round_flow(self):
        rules = Rules()
        r = Round(stacked('9S 9H', '4D 4C', '2S 5H KD 7C 3S'), rules, 10).deal()
        self.assertEqual(r.state, DECIDING)
        self.assertEqual(len(r.flop()), 3)
        with self.assertRaises(ValueError):
            r.call_(3)
        r.call_(4)
        self.assertEqual((r.state, r.outcome, r.net, r.call), (DONE, WIN, 10 + 40, 40))
        r = Round(stacked('9S 9H', '4D 4C', '2S 5H KD 7C 3S'), rules, 10, mult=3).deal()
        r.call_(2)
        self.assertEqual(r.net, 10 + 20 * 3)
        self.assertTrue(r.beat_qualified())
        r = Round(stacked('9S 9H', '4D 4C', '2S 5H KD 7C 3S'), rules, 10).deal()
        r.fold()
        self.assertEqual((r.outcome, r.net, r.qualified), (FOLD, -10, True))
        self.assertFalse(r.beat_qualified())
        with self.assertRaises(ValueError):
            r.fold()


class TableTests(unittest.TestCase):
    def test_ante_limits_against_the_exposure(self):
        t = CaribbeanTable(random.Random(1), Bankroll(1000), seats=0)
        self.assertEqual(t.exposure, 5)
        self.assertEqual(t.adjust_ante(1000), 50)
        self.assertEqual(t.adjust_ante(-1000), 5)
        t = CaribbeanTable(random.Random(1), Bankroll(120), seats=0)
        self.assertEqual(t.adjust_ante(1000), 20)                     # 120 // 5 = 24 -> 20
        t = CaribbeanTable(random.Random(1), Bankroll(24), seats=0)
        self.assertEqual(t.state, BROKE)
        t.refill()
        self.assertEqual((t.state, t.bankroll.balance, t.bankroll.bet), (BETTING, 1000, MIN_ANTE))

    def test_hand_and_stakes(self):
        t = CaribbeanTable(random.Random(1), Bankroll(1000), seats=0)
        t.adjust_ante(5)                                              # 10
        t.shoe = stacked('9S 9H', '4D 4C', '2S 5H KD 7C 3S')
        t.deal()
        self.assertEqual(t.stakes(), (990, 10, 0))
        t.call(4)
        self.assertEqual((t.state, t.bankroll.balance), (RESULT, 1050))
        self.assertEqual(t.stakes(), (1050, 10, 40))
        self.assertFalse(t.armed)                                     # no seats: no multiplier
        t.next_hand()
        t.shoe = stacked('2S 3H', '4D 4C', '7S 8H KD 7C 9S')
        t.deal()
        t.fold()
        self.assertEqual(t.bankroll.balance, 1040)
        t.next_hand()
        t.shoe = stacked('2S 3H', '5D 6C', '7S 8H KD 7C 9S')           # dealer pair of 7s on board... see below
        t.deal()
        t.call(2)
        # player 2-3 + board 7 7 8 9 K = pair of 7s; dealer 5-6 + board = 5-6-7-8-9 straight: qualifies, loses 30
        self.assertEqual((t.round.outcome, t.bankroll.balance), (LOSE, 1010))

    def test_unqualified_dealer_pushes_everything(self):
        t = CaribbeanTable(random.Random(1), Bankroll(1000), seats=0)
        t.shoe = stacked('AS AH', '2D 3C', '7S 8H KD TC 4S')
        t.deal()
        t.call(4)
        self.assertEqual((t.round.outcome, t.round.qualified, t.bankroll.balance), (PUSH, False, 1000))

    def test_multiplier_arms_only_when_everyone_beats_a_qualified_dealer(self):
        t = CaribbeanTable(random.Random(1), Bankroll(1000), seats=4)
        # player AA, dealer 44 (qualifies), board nothing; seats get pocket pairs above fours
        t.shoe = stacked('AS AH', '4D 4C', '7S 8H KD TC 2S KS KH QS QH JS JH 9S 9H')
        t.deal()
        self.assertEqual(t.seats.calls, [4, 4, 4, 4])
        t.call(4)
        self.assertTrue(t.seats.all_won())
        self.assertTrue(t.armed)
        self.assertEqual(t.multiplier(), 3)                           # five at the table, capped at 3
        t.next_hand()
        t.shoe = stacked('AS AH', '4D 4C', '7S 8H KD TC 2S 5S 5H 6S 6H QS QH JS JH')
        t.deal()
        self.assertEqual(t.round.mult, 3)
        t.call(2)
        self.assertEqual(t.round.net, 5 + 10 * 3)                     # Ante 1:1 (two pair... no: pair of aces 1:1) + call x3
        self.assertTrue(t.armed)                                      # everyone won again
        t.next_hand()
        # a seat that folds breaks the chain
        t.shoe = stacked('AS AH', '4D 4C', '7S 8H KD TC 2S 3S 5H 6S 6H QS QH JS JH')
        t.deal()
        self.assertEqual(t.seats.calls[0], 0)                         # 3-5 against 7 8 K: fold
        t.call(4)
        self.assertFalse(t.armed)
        t.next_hand()
        self.assertEqual(t.multiplier(), 1)

    def test_multiplier_never_arms_on_an_unqualified_dealer(self):
        t = CaribbeanTable(random.Random(1), Bankroll(1000), seats=4)
        t.shoe = stacked('AS AH', '2D 3C', '7S 8H KD TC 4S KS KH QS QH JS JH 9S 9H')
        t.deal()
        t.call(4)
        self.assertEqual(t.round.outcome, PUSH)
        self.assertFalse(t.armed)

    def test_seats_never_touch_the_player(self):
        t = CaribbeanTable(random.Random(7), Bankroll(1000), seats=4)
        t0 = CaribbeanTable(random.Random(7), Bankroll(1000), seats=0)
        for _ in range(40):
            t.deal()
            t0.deal()
            self.assertEqual(t.round.player, t0.round.player)
            self.assertEqual(t.round.dealer, t0.round.dealer)
            self.assertEqual(t.round.board, t0.round.board)
            a = advice(t.round.player, t.round.flop())
            for x in (t, t0):
                if a is None:
                    x.fold()
                else:
                    x.call(x.rules.high if a == HIGH else x.rules.low)
            # the multiplier is the one thing the seats change for the player: compare without it
            self.assertEqual(t.round.outcome, t0.round.outcome)
            if t.round.mult == 1:
                self.assertEqual(t.round.net, t0.round.net)
            t.next_hand()
            t0.next_hand()
            if t.state != BETTING or t0.state != BETTING:
                break


if __name__ == '__main__':
    unittest.main()
