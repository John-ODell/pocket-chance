# DR-014: Blackjack bet limits

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-03
- **Blocks:** Betting screen
- **Needs HW review:** no

## The decision
Minimum bet, maximum bet and how the bet changes.

## Why it matters
Chips are 1, 5, 25, 100 and 500 in the art spec. The bet size changes the pace of the game and the rounding on blackjack (see DR-010).

## Options
### A. Minimum 5, maximum 500 (or the bankroll if lower), steps of 5 (recommended)
- Pros: matches the larger chips; blackjack pays whole numbers for even multiples of 10 and loses at most half a chip otherwise.
- Cons: `chip_1` art is not needed; John can skip it.

### B. Minimum 1, maximum 500, steps of 1
- Cons: many button presses to reach a normal bet; more half-chip rounding.

### C. Minimum 10, maximum 1000
- Cons: `chip_500` stops being the top chip; larger swings.

## Recommendation
Option A. A double down is allowed only when the bankroll covers the extra bet. These limits do not change the house edge, which stays about 0.95% of the amount bet (DR-009, DR-010).

## What John would have to do or accept
Skip `chip_1.bmp`, or keep it for a later use.
