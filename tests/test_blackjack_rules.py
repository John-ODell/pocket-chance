import random
import unittest

import tests.context  # noqa: F401
from cards import card_from_name, hand_value, Shoe
from blackjack_rules import (Rules, Round, dealer_should_hit, is_blackjack, payout,
                             BLACKJACK, WIN, LOSE, PUSH, BUST, PLAYER, DONE)


def h(*names):
    return [card_from_name(n) for n in names]


def play(deal_order, rules=None, bet=10):
    """Round on a stacked shoe. Deal order: player, dealer up, player, dealer hole, then draws."""
    rules = rules or Rules()
    return Round(Shoe(rules.decks, random.Random(0), stacked=h(*deal_order)), rules, bet)


class DealerRule(unittest.TestCase):
    def test_hits_16_and_below(self):
        for hand in (['TS', '6H'], ['2S', '3H'], ['AS', '5H'], ['AS', 'AH', '4C']):
            self.assertTrue(dealer_should_hit(h(*hand), False), hand)
            self.assertTrue(dealer_should_hit(h(*hand), True), hand)

    def test_stands_18_and_above(self):
        for hand in (['TS', '8H'], ['AS', '7H'], ['AS', '9H'], ['TS', 'KH']):
            self.assertFalse(dealer_should_hit(h(*hand), False), hand)
            self.assertFalse(dealer_should_hit(h(*hand), True), hand)

    def test_hard_17_always_stands(self):
        self.assertFalse(dealer_should_hit(h('TS', '7H'), False))
        self.assertFalse(dealer_should_hit(h('TS', '7H'), True))
        self.assertFalse(dealer_should_hit(h('AS', '6H', 'TC'), True))

    def test_soft_17_depends_on_rule(self):
        for hand in (['AS', '6H'], ['AS', 'AH', '5C'], ['AS', '2H', '4C']):
            self.assertFalse(dealer_should_hit(h(*hand), False), hand)   # S17
            self.assertTrue(dealer_should_hit(h(*hand), True), hand)     # H17


class Payouts(unittest.TestCase):
    def test_three_to_two(self):
        r = Rules(bj_num=3, bj_den=2)
        self.assertEqual(payout(10, BLACKJACK, r), 15)
        self.assertEqual(payout(100, BLACKJACK, r), 150)

    def test_six_to_five(self):
        r = Rules(bj_num=6, bj_den=5)
        self.assertEqual(payout(10, BLACKJACK, r), 12)
        self.assertEqual(payout(100, BLACKJACK, r), 120)

    def test_odd_bets_round_down(self):
        self.assertEqual(payout(5, BLACKJACK, Rules(bj_num=3, bj_den=2)), 7)
        self.assertEqual(payout(1, BLACKJACK, Rules(bj_num=3, bj_den=2)), 1)
        self.assertEqual(payout(1, BLACKJACK, Rules(bj_num=6, bj_den=5)), 1)

    def test_even_money_and_losses(self):
        r = Rules()
        self.assertEqual(payout(25, WIN, r), 25)
        self.assertEqual(payout(25, PUSH, r), 0)
        self.assertEqual(payout(25, LOSE, r), -25)
        self.assertEqual(payout(25, BUST, r), -25)


class IsBlackjack(unittest.TestCase):
    def test(self):
        self.assertTrue(is_blackjack(h('AS', 'KH')))
        self.assertTrue(is_blackjack(h('TD', 'AC')))
        self.assertFalse(is_blackjack(h('7S', '7H', '7C')))   # 21 in three cards
        self.assertFalse(is_blackjack(h('9S', 'KH')))


class RoundFlow(unittest.TestCase):
    def test_player_blackjack_pays_rule(self):
        r = play(['AS', '9D', 'KH', '7C']).deal()
        self.assertEqual((r.state, r.outcome, r.net), (DONE, BLACKJACK, 15))
        r = play(['AS', '9D', 'KH', '7C'], Rules(bj_num=6, bj_den=5)).deal()
        self.assertEqual(r.net, 12)

    def test_both_blackjack_push(self):
        r = play(['AS', 'KD', 'KH', 'AC']).deal()
        self.assertEqual((r.outcome, r.net), (PUSH, 0))

    def test_dealer_blackjack_peek(self):
        r = play(['9S', 'AD', '8H', 'KC']).deal()
        self.assertEqual((r.state, r.outcome, r.net), (DONE, LOSE, -10))

    def test_dealer_ten_up_blackjack_peek(self):
        r = play(['9S', 'KD', '8H', 'AC']).deal()
        self.assertEqual((r.outcome, r.net), (LOSE, -10))

    def test_no_peek_dealer_blackjack_resolved_after_player_acts(self):
        r = play(['9S', 'AD', '8H', 'KC'], Rules(dealer_peeks=False)).deal()
        self.assertEqual(r.state, PLAYER)
        r.stand()
        self.assertEqual((r.outcome, r.net), (LOSE, -10))

    def test_player_bust_dealer_does_not_draw(self):
        r = play(['TS', '9D', '6H', '8C', 'KD']).deal()
        self.assertEqual(r.state, PLAYER)
        self.assertTrue(r.hole_hidden())
        r.hit()
        self.assertEqual((r.state, r.outcome, r.net), (DONE, BUST, -10))
        self.assertEqual(len(r.dealer), 2)
        self.assertFalse(r.hole_hidden())

    def test_stand_dealer_draws_to_17_and_busts(self):
        r = play(['TS', '6D', '8H', '5C', 'KD']).deal()   # dealer 11? 6+5 -> hits K -> 21
        r.stand()
        self.assertEqual((r.outcome, r.net), (LOSE, -10))
        r = play(['TS', '6D', '8H', 'TC', 'KD']).deal()   # dealer 16 -> hits K -> 26
        r.stand()
        self.assertEqual((r.outcome, r.net), (WIN, 10))

    def test_win_lose_push_on_totals(self):
        r = play(['TS', 'TD', '9H', '8C']).deal().stand()    # 19 v 18
        self.assertEqual(r.outcome, WIN)
        r = play(['TS', 'TD', '8H', '9C']).deal().stand()    # 18 v 19
        self.assertEqual(r.outcome, LOSE)
        r = play(['TS', 'TD', '9H', '9C']).deal().stand()    # 19 v 19
        self.assertEqual((r.outcome, r.net), (PUSH, 0))

    def test_h17_dealer_hits_soft_17(self):
        order = ['TS', 'AD', '8H', '6C', '2D']   # player 18, dealer soft 17, then draws 2
        r = play(order, Rules(hit_soft_17=True)).deal().stand()
        self.assertEqual(len(r.dealer), 3)      # 19, beats 18
        self.assertEqual(r.outcome, LOSE)
        r = play(order, Rules(hit_soft_17=False)).deal().stand()
        self.assertEqual(len(r.dealer), 2)      # stood on soft 17, player 18 wins
        self.assertEqual(r.outcome, WIN)

    def test_auto_stand_on_21(self):
        r = play(['5S', 'TD', '6H', '8C', 'TH']).deal()   # player 11, hit ten -> 21
        r.hit()
        self.assertEqual(r.state, DONE)
        self.assertEqual(r.outcome, WIN)    # dealer 18

    def test_double_wins_double(self):
        r = play(['5S', 'TD', '6H', '8C', 'TH']).deal()
        self.assertTrue(r.can_double())
        r.double()
        self.assertEqual((r.outcome, r.bet, r.net), (WIN, 20, 20))
        self.assertEqual(len(r.player), 3)

    def test_double_loses_double_and_busts(self):
        r = play(['TS', 'TD', '6H', '8C', 'KD']).deal()
        r.double()
        self.assertEqual((r.outcome, r.net), (BUST, -20))

    def test_cannot_double_after_hit_or_when_over(self):
        r = play(['2S', 'TD', '3H', '7C', '2D', '9D']).deal()
        r.hit()
        self.assertFalse(r.can_double())
        with self.assertRaises(ValueError):
            r.double()
        r.stand()
        with self.assertRaises(ValueError):
            r.hit()

    def test_double_restricted_rule(self):
        rules = Rules(double_any_two=False)
        self.assertFalse(play(['TS', '5D', '8H', '6C'], rules).deal().can_double())   # 18
        self.assertTrue(play(['5S', '5D', '5H', '6C'], rules).deal().can_double())    # hard 10
        self.assertFalse(play(['AS', '5D', '4H', '6C'], rules).deal().can_double())   # soft 15

    def test_blackjack_not_awarded_for_21_in_three(self):
        r = play(['5S', '9D', '6H', '8C', 'TH']).deal()   # 5+6+10 = 21, dealer 17
        r.hit()
        self.assertEqual((r.outcome, r.net), (WIN, 10))


class Simulation(unittest.TestCase):
    def test_random_rounds_always_finish_and_balance(self):
        rng = random.Random(5)
        rules = Rules()
        shoe = rules.new_shoe(rng)
        for _ in range(2000):
            if shoe.needs_shuffle():
                shoe.shuffle()
            r = Round(shoe, rules, 10).deal()
            while r.state == PLAYER:
                if hand_value(r.player)[0] < 15:
                    r.hit()
                else:
                    r.stand()
            self.assertIn(r.outcome, (BLACKJACK, WIN, LOSE, PUSH, BUST))
            self.assertIn(r.net, (15, 10, 0, -10))


if __name__ == '__main__':
    unittest.main()
