import random
import unittest

import tests.context  # noqa: F401
from bankroll import Bankroll
from slots_rules import exact_stats, strip, STAR, CHERRY
from slots_table import (SlotsTable, SpinPlan, default_reels, default_paytable, COUNTS, BETTING, RESULT, BROKE,
                         MIN_BET, MAX_BET, SYM_PX, FAST, SLOW)


class ApprovedConfig(unittest.TestCase):
    def test_rtp_is_the_ruled_one(self):
        st = exact_stats([strip(COUNTS)] * 3, default_paytable())
        self.assertAlmostEqual(st['rtp'], 0.9384, places=3)        # DR-018 option A
        self.assertEqual(default_paytable().top_prize(), (STAR, 1000))


class Plan(unittest.TestCase):
    def run_plan(self, stops):
        p = SpinPlan(32, stops)
        frames = 0
        change_frames = [[] for _ in stops]
        stop_frame = [None] * len(stops)
        last_pos = list(p.pos)
        while not p.step():
            frames += 1
            for i in range(len(stops)):
                self.assertTrue(0 <= p.pos[i] - last_pos[i] <= FAST, 'speed')
                if p.changed[i]:
                    change_frames[i].append(p.frame)
                if stop_frame[i] is None and not p.moving(i):
                    stop_frame[i] = p.frame
            last_pos = list(p.pos)
            self.assertLess(frames, 1000)
        for i in range(len(stops)):
            if stop_frame[i] is None:
                stop_frame[i] = p.frame
        return p, change_frames, stop_frame

    def test_ends_on_the_stops(self):
        for stops in ([0, 0, 0], [31, 15, 7], [5, 5, 5], [3, 30, 12]):
            p, _, _ = self.run_plan(stops)
            self.assertEqual(p.top, stops)
            self.assertEqual(p.off, [0, 0, 0])
            self.assertTrue(p.done)

    def test_reels_stop_left_to_right_and_apart(self):
        p, changes, stop = self.run_plan([4, 9, 20])
        self.assertLess(stop[0], stop[1])
        self.assertLess(stop[1], stop[2])
        self.assertGreaterEqual(stop[1] - stop[0], 15)           # about 0.3-0.4 s at 50 fps
        self.assertGreaterEqual(stop[2] - stop[1], 15)
        self.assertLess(stop[2], 160)                            # whole spin under ~3.2 s at 50 fps

    def test_symbol_changes_never_share_a_frame_at_full_speed(self):
        p, changes, stop = self.run_plan([4, 9, 20])
        fast_end = min(stop) - SYM_PX // SLOW                     # before any reel slows down
        seen = set()
        for i in range(3):
            for f in changes[i]:
                if f < fast_end:
                    self.assertNotIn(f, seen, 'two reels loaded a symbol on frame %d' % f)
                    seen.add(f)

    def test_slow_phase_is_the_last_symbol(self):
        p = SpinPlan(32, [0, 0, 0])
        speeds = []
        while not p.step():
            if p.moving(0) or p.off[0] or True:
                pass
            speeds.append(p.pos[0])
        diffs = [b - a for a, b in zip(speeds, speeds[1:]) if b != a]
        self.assertEqual(diffs[0], FAST)
        self.assertEqual(diffs[-1], SLOW)
        self.assertEqual(sum(1 for d in diffs if d == SLOW), SYM_PX // SLOW)

    def test_first_frame_shows_a_real_strip_symbol(self):
        p = SpinPlan(32, [7, 8, 9])
        self.assertTrue(all(0 <= t < 32 for t in p.top))


class TableFlow(unittest.TestCase):
    def table(self, balance=1000):
        return SlotsTable(random.Random(5), Bankroll(balance))

    def test_bet_limits(self):
        t = self.table()
        self.assertEqual(t.bankroll.bet, MIN_BET)
        self.assertEqual(t.adjust_bet(1000), MAX_BET)
        self.assertEqual(t.adjust_bet(-1000), MIN_BET)
        t.adjust_bet(25)
        self.assertEqual(t.bankroll.bet, 30)
        t2 = self.table(balance=47)
        self.assertEqual(t2.adjust_bet(1000), 45)

    def test_shared_bankroll_bet_is_pulled_into_range(self):
        b = Bankroll(1000)
        b.bet = 500                                  # left over from blackjack
        t = SlotsTable(random.Random(1), b)
        self.assertEqual(b.bet, MAX_BET)

    def test_spin_moves_balance_and_matches_paytable(self):
        t = self.table()
        t.adjust_bet(5)                              # bet 10
        for _ in range(300):
            bet = t.bankroll.bet                     # the refill resets it to the minimum
            win, label = t.spin()
            self.assertEqual(t.state, RESULT)
            self.assertEqual((win, label), t.reels.paytable.evaluate(t.reels.line(), bet))
            self.assertEqual(t.last, (win, label))
            plan = t.plan()
            while not plan.step():
                pass
            self.assertEqual(plan.top, t.reels.stops)
            t.next()
            if t.state == BROKE:
                t.refill()
        self.assertIn(t.state, (BETTING, BROKE))

    def test_balance_arithmetic(self):
        t = self.table(balance=100)
        bal = 100
        for _ in range(50):
            if t.state == BROKE:
                t.refill()
                bal = 1000
            bet = t.bankroll.bet
            win, _ = t.spin()
            bal += win - bet
            self.assertEqual(t.bankroll.balance, bal)
            t.next()

    def test_broke_and_refill(self):
        t = self.table(balance=4)
        self.assertEqual(t.state, BROKE)
        with self.assertRaises(ValueError):
            t.spin()
        t.refill()
        self.assertEqual((t.state, t.bankroll.balance, t.bankroll.bet), (BETTING, 1000, MIN_BET))

    def test_wrong_state_calls(self):
        t = self.table()
        with self.assertRaises(ValueError):
            t.next()
        with self.assertRaises(ValueError):
            t.refill()
        t.spin()
        with self.assertRaises(ValueError):
            t.adjust_bet(5)

    def test_paytable_rows(self):
        rows = self.table().paytable_rows(10)
        self.assertEqual(rows[0], ('3 x star', 10000))
        self.assertEqual(rows[-1], ('1 cherry', 10))
        self.assertEqual(len(rows), 10)


if __name__ == '__main__':
    unittest.main()
