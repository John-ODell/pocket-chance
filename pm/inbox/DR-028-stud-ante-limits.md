# DR-028: Caribbean Stud: ante limits against the shared bankroll

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-05
- **Blocks:** Caribbean Stud screen
- **Needs HW review:** no

## The decision
The minimum and maximum ante, given that a raise commits two more antes (3x exposure per hand).

## Options
### A. Ante 5 to 100 in steps of 5, raise allowed only if the bankroll covers ante + raise (recommended)
- The ante may not exceed a third of the bankroll (rounded down to 5), so a raise is always affordable when the hand is dealt; with the 1000-chip start the most a hand can lose is 300.
- Shared `$` balance and chip art with blackjack; a fold still saves (the balance changed).
- Pros: the player can never be dealt a hand they cannot play out; exposure stays under a third of the start bankroll.
- Cons: a 100 ante cap is lower than blackjack's 500 bet cap; the 3x exposure is the reason.

### B. Ante 5 to 500 like blackjack
- Cons: a 500 ante exposes 1500, more than the starting bankroll; the raise would often be unaffordable and the game would have to refuse it, which is unfair after the deal.

### C. Allow the deal when only the ante is covered, and refuse the raise later
- Cons: the player learns too late that they cannot raise a good hand. Rejected.

## Recommendation
Option A. The house edge does not depend on the ante size.

## What John would have to do or accept
Antes of 5 to 100. Blackjack's limits are unchanged.
