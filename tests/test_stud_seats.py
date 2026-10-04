import random
import unittest

import tests.context  # noqa: F401
from bankroll import Bankroll
from cards import Shoe, card_from_name
from poker import evaluate5
from stud_rules import Rules, resolve, advice, new_deck, FOLD, WIN, LOSE, PUSH, NOQUALIFY
from stud_seats import Seats, START
from stud_table import StudTable, RESULT


class SeatsLogic(unittest.TestCase):
    def test_deal_uses_the_shared_deck(self):
        shoe = new_deck(random.Random(1))
        shoe.shuffle()
        seen = [shoe.draw() for _ in range(10)]          # player and dealer
        seats = Seats(5)
        seats.deal(shoe)
        all_cards = seen + [c for h in seats.hands for c in h]
        self.assertEqual(len(all_cards), 35)
        self.assertEqual(len(set(all_cards)), 35)        # no card dealt twice
        self.assertEqual(seats.delta, [0] * 5)

    def test_count_clamped_and_zero_seats(self):
        self.assertEqual(Seats(9).count, 5)
        self.assertEqual(Seats(-1).count, 0)
        s = Seats(0)
        shoe = new_deck(random.Random(1))
        s.deal(shoe)
        self.assertEqual(shoe.remaining(), 52)

    def test_settle_matches_the_player_rules(self):
        rules = Rules()
        dealer = [card_from_name(n) for n in 'KH KD 5C 3D 2D'.split()]
        dv = evaluate5(dealer)
        seats = Seats(3)
        seats.hands = [[card_from_name(n) for n in h.split()] for h in
                       ('9S 9D 4C 3H 2S', 'AS AD AC 3H 2S', 'QS JD 4C 3H 2S')]
        seats.settle(dealer, dv, 10, rules)
        # pair of 9s raises and loses 30; trips raise and win 10 + 20 x 3; queen-high folds -10
        self.assertEqual(seats.delta, [-30, 70, -10])
        self.assertEqual(seats.chips, [970, 1070, 990])

    def test_no_qualify_pays_every_raiser(self):
        rules = Rules()
        dealer = [card_from_name(n) for n in 'KH 7D 5C 3D 2D'.split()]
        seats = Seats(2)
        seats.hands = [[card_from_name(n) for n in h.split()] for h in ('9S 9D 4C 3H 2S', 'AS KD 4C 3H 2S')]
        seats.settle(dealer, evaluate5(dealer), 10, rules)
        self.assertEqual(seats.delta[0], 10)
        # A-K against a king up-card with no match and no queen/jack: basic strategy folds
        self.assertEqual(seats.delta[1], -10)

    def test_silent_refill(self):
        seats = Seats(1)
        seats.chips = [20]
        dealer = [card_from_name(n) for n in 'KH KD 5C 3D 2D'.split()]
        seats.hands = [[card_from_name(n) for n in '9S 9D 4C 3H 2S'.split()]]
        seats.settle(dealer, evaluate5(dealer), 10, Rules())
        self.assertEqual(seats.chips, [START - 30])

    def test_stack_height(self):
        s = Seats(1)
        for chips, h in ((0, 0), (199, 0), (200, 1), (1000, 5), (1399, 6), (5000, 6)):
            s.chips = [chips]
            self.assertEqual(s.stack_height(0), h, chips)


class TableWithSeats(unittest.TestCase):
    def test_seats_follow_the_hands_and_never_touch_the_player(self):
        rng = random.Random(7)
        t = StudTable(rng, Bankroll(1000), seats=5)
        # the same deck order with no seats gives the player the same cards
        t0 = StudTable(random.Random(7), Bankroll(1000), seats=0)
        for _ in range(30):
            t.deal()
            t0.deal()
            self.assertEqual(t.round.player, t0.round.player)
            self.assertEqual(t.round.dealer, t0.round.dealer)
            t.raise_()
            t0.raise_()
            self.assertEqual(t.round.net, t0.round.net)
            self.assertEqual(t.state, RESULT)
            self.assertTrue(all(d != 0 for d in t.seats.delta))      # every seat settled
            total = sum(t.seats.chips)
            self.assertGreater(total, 0)
            t.next_hand()
            t0.next_hand()
            if t.state != 'betting':
                break

    def test_fold_still_settles_the_seats(self):
        t = StudTable(random.Random(2), Bankroll(1000))
        t.deal()
        t.fold()
        self.assertTrue(all(d != 0 for d in t.seats.delta))
        t.next_hand()
        t.deal()
        self.assertEqual(t.seats.delta, [0] * 5)                     # markers cleared at the deal


if __name__ == '__main__':
    unittest.main()
