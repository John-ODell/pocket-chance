# DR-009: Blackjack dealer rule: stand or hit on soft 17

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-03
- **Blocks:** Nothing, it is a parameter in the rules engine (`hit_soft_17`, default stand)
- **Needs HW review:** no

## The decision
Does the dealer stand or hit on a "soft 17" (a 17 counting an ace as 11, such as Ace + 6)?

## Why it matters
It changes the house edge by about a third of a percentage point.

## Options
### A. Dealer stands on all 17 (S17) (recommended)
- Pros: the simpler rule, and a little kinder to the player.
- House edge, measured in my simulation (6 decks, 3:2, no splitting, basic strategy): about 0.95%. RTP about 99.05%.

### B. Dealer hits soft 17 (H17)
- Pros: the rule many casinos use.
- House edge in the same simulation: about 1.29%. RTP about 98.7%.

## Recommendation
Option A. A handheld toy should feel fair, and the rule is easier to explain on screen. I would change my mind if John wants it to match a specific casino.

## What John would have to do or accept
The house edge is about 1% either way. Over many hands the bankroll drifts down slowly.

## Appendix
Simulation: `tools/bj_edge.py`, 3 million hands per row, noise about plus or minus 0.1 points. Perfect basic strategy without splitting. A casual player will do worse. Other rows: 1 deck S17 3:2 -0.58%; 2 decks S17 3:2 -0.96%; 6 decks H17 6:5 -2.52%.
