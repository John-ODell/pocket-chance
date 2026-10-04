# DR-059: Baccarat: the Banker commission in whole chips

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-06
- **Blocks:** The baccarat engine (needed with DR-051)
- **Needs HW review:** no

## The decision
How the 5% Banker commission is taken when chips are whole numbers and stakes move in fives.

## Why it matters
5% of a 5-chip stake is a quarter chip. Rounding the commission down would pay a 5-chip Banker win in full, giving the player a 1.2% advantage on small Banker bets, which a game must not do. Rounding up makes small Banker bets expensive. The choice sets the real edge at each stake.

## Options
### A. Pay the whole-chip part of 19/20 of the stake: commission rounded up (recommended)
- A Banker win pays `stake * 19 // 20`: 4 on 5, 9 on 10, 14 on 15, 19 on 20, 23 on 25, 47 on 50, 95 on 100.
- Real Banker edge by stake (calculated from the exact outcome frequencies, `tools/baccarat_edge.py`): **5: 7.9%, 10: 3.4%, 15: 1.8%, 20: 1.06%, 25: 2.4%, 30: 1.8%, 40: 1.06%, 50: 1.5%, 60: 1.06%, 80: 1.06%, 100: 1.06%.** At any multiple of 20 it is exactly the published 1.06%; the Player bet is 1.24% at every stake.
- The help screen says "19 for 20, rounded down" (DR-058).
- Pros: the joystick works exactly as in the other games; the house never pays more than the real commission allows; the small-stake penalty is the same one a casino applies with its chip minimums.
- Cons: Banker at 5 or 10 is a poor bet (7.9%, 3.4%); the help screen's "1.1%" is true at 20, 40, 60, 80 and 100.

### B. Banker stakes move in twenties (20, 40, 60, 80, 100)
- Pros: the commission is always a whole number; the edge is 1.06% at every allowed stake.
- Cons: the joystick jumps by 20 on Banker and by 5 elsewhere; the Banker minimum is four times the Player minimum; more code and a confusing feel.

### C. The no-commission variant (DR-051 option C) instead of a commission
- A Banker win on a total of 6 pays half: 2 on 5 (2.5 rounded down), 5 on 10, exact at multiples of 10. Edge 1.46% at multiples of 10, about 2.0% at 5.
- Cons: a different game from the one John knows; only moves the rounding problem to one outcome.

### D. Keep fractional chips in the bankroll
- Cons: every screen, save and test assumes whole chips. Rejected.

## Recommendation
Option A. It is what every home or app version of the game does, and the published edge holds at the stakes a Banker bettor will actually use. Option B would change my mind if John wants the published 1.06% to be true at every Banker stake and accepts the uneven joystick.

## What John would have to do or accept
A Banker win pays 19 chips for every 20 staked, rounded down to whole chips; at 5 or 10 chips the Banker bet is worse than the Player bet.
