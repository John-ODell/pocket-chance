# John's repro path: bank 966 (his save), seats 4, first hands after the menu, ante 15 or 20, HIGH call.
import sys, random, types, collections
sys.argv = ['x']; exec(open(sys.path[0] + '/fuzz.py').read().split('from bankroll import Bankroll')[0])
from bankroll import Bankroll
import caribbean
from caribbean_table import BETTING, DECIDING, RESULT, BROKE
out = collections.Counter(); worst = 0
for seed in range(20000):
    ctx = types.SimpleNamespace(lcd=LCD(), assets=Assets(), buttons=Buttons(), store=Store(),
                                rng=random.Random(seed), bankroll=Bankroll(966), car_seats=4)
    scr = caribbean.Screen(ctx); scr.draw_all()
    ante = 15 if seed % 2 else 20
    for _ in range((ante - 5) // 5): assert scr.handle('UP')
    assert scr.table.bankroll.bet == ante, scr.table.bankroll.bet
    for hand in range(3):                                  # first three hands: deal, HIGH, next
        assert scr.handle('A') and scr.table.state == DECIDING
        assert scr.table.round.ante == ante
        assert scr.handle('A') and scr.table.state == RESULT, scr.table.state
        r = scr.table.round
        out[(r.outcome, r.mult, r.qualified)] += 1
        assert scr.handle('A') and scr.table.state in (BETTING, BROKE)
        if scr.table.state == BROKE: break
print("RESULT targeted_ok seeds=20000 ante=15/20 bank=966 seats=4 three HIGH hands each; outcomes:", dict(out))
