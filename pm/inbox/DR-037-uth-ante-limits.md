# DR-037: Ultimate Texas Hold'em: Ante limits against the 6x exposure

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-05
- **Blocks:** Hold'em screen
- **Needs HW review:** no

## The decision
The Ante range, given that Ante + Blind + a 4x Play bet commits six Antes.

## Options
### A. Ante 5 to 50 in steps of 5, capped at a sixth of the bankroll (recommended)
- The Blind equals the Ante; a 4x raise is always affordable when the hand is dealt; with the 1000-chip start the most a hand can lose is 300 (the same ceiling as Caribbean Stud's 3 x 100).
- Broke below 30 chips (6 x the minimum Ante).

### B. Ante 5 to 100 (exposure 600)
- Cons: one bad hand can take 60% of the starting bankroll.

### C. Ante 5 to 100 but refuse the 4x raise when it is not covered
- Cons: the player learns too late that the best raise is unavailable. Rejected (same reasoning as Stud, DR-028).

## Recommendation
Option A. The house edge does not depend on the Ante.

## What John would have to do or accept
Antes of 5 to 50 at Hold'em (Stud 5 to 100, blackjack 5 to 500), each set by its exposure so a hand can never cost more than 300 from the 1000 start.
