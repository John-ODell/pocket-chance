"""Baccarat chip-stack seats (DR-055): habits, settling, and never touching the player."""
import random
import unittest

import tests.context  # noqa: F401
from bankroll import Bankroll
from baccarat_rules import PLAYER, BANKER, TIE
from baccarat_seats import Seats, START, STAKE
from baccarat_table import BaccaratTable


class SeatsLogic(unittest.TestCase):
    def test_count_clamped(self):
        self.assertEqual(Seats(9).count, 5)
        self.assertEqual(Seats(-1).count, 0)
        s = Seats(0)
        s.place()
        s.settle(PLAYER)
        self.assertEqual(s.chips, [])

    def test_habits(self):
        s = Seats(5)
        s.place()                                                   # first coup: no winner yet, "last" = Banker
        self.assertEqual(s.sides, [BANKER, PLAYER, BANKER, PLAYER, BANKER])
        s.settle(PLAYER)
        s.place()
        self.assertEqual(s.sides, [BANKER, PLAYER, PLAYER, BANKER, BANKER])   # follow / against the Player win
        s.settle(TIE)                                               # a tie leaves "last" alone
        s.place()
        self.assertEqual(s.sides[2:4], [PLAYER, BANKER])
        s.settle(BANKER)
        s.place()                                                   # coup 4
        self.assertEqual(s.sides[2:], [BANKER, PLAYER, BANKER])
        s.settle(BANKER)
        s.place()                                                   # coup 5: seat 4 bets Tie
        self.assertEqual(s.sides[4], TIE)

    def test_settle_uses_the_player_pays(self):
        s = Seats(5)
        s.place()                                                   # B, P, B, P, B
        s.settle(BANKER)
        self.assertEqual(s.delta, [19, -20, 19, -20, 19])
        self.assertEqual(s.chips, [1019, 980, 1019, 980, 1019])
        self.assertEqual(s.settled, [True] * 5)
        s.place()
        self.assertEqual(s.delta, [0] * 5)
        self.assertEqual(s.settled, [False] * 5)
        s.settle(TIE)                                               # side bets push: delta 0 but settled
        self.assertEqual(s.delta, [0] * 5)
        self.assertEqual(s.settled, [True] * 5)

    def test_tie_seat_wins_eight_to_one(self):
        s = Seats(5)
        for _ in range(5):
            s.place()
        self.assertEqual(s.sides[4], TIE)
        s.settle(TIE)
        self.assertEqual(s.delta[4], 8 * STAKE)

    def test_silent_refill(self):
        s = Seats(1)
        s.chips = [15]
        s.place()
        s.settle(PLAYER)                                            # seat 0 is on Banker: loses 20 after the refill
        self.assertEqual(s.chips, [START - STAKE])

    def test_stack_height(self):
        s = Seats(1)
        for chips, h in ((0, 0), (199, 0), (200, 1), (1000, 5), (1399, 6), (5000, 6)):
            s.chips = [chips]
            self.assertEqual(s.stack_height(0), h, chips)


class TableWithSeats(unittest.TestCase):
    def test_seats_never_touch_the_player(self):
        t = BaccaratTable(random.Random(7), Bankroll(1000), seats=5)
        t0 = BaccaratTable(random.Random(7), Bankroll(1000), seats=0)
        for _ in range(40):
            t.deal()
            t0.deal()
            self.assertEqual(t.coup.player, t0.coup.player)
            self.assertEqual(t.coup.banker, t0.coup.banker)
            self.assertEqual(t.net, t0.net)
            self.assertEqual(t.bankroll.balance, t0.bankroll.balance)
            self.assertEqual(t.seats.settled, [True] * 5)
            t.next_coup()
            t0.next_coup()


if __name__ == '__main__':
    unittest.main()
