# DR-013: Starting bankroll and what happens when the player is broke

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-03
- **Blocks:** Bankroll module defaults, blackjack betting screen
- **Needs HW review:** no

## The decision
How many chips a new player starts with, and what happens when they cannot cover the minimum bet.

## Why it matters
There is no real money, so a dead end (broke forever) just ends the fun.

## Options
### A. Start at 1000 chips; when broke, offer a fresh 1000 (recommended)
- When the bankroll is below the minimum bet, show "Out of chips. A: start over with 1000". It resets the bankroll only, nothing else.
- Pros: never stuck; clear moment of loss. Note this is not a house-edge matter; the starting amount only sets how long play lasts.
- With a 5-chip bet and a 1% edge you lose about 0.05 chips per hand on average, so 1000 chips lasts a very long time.

### B. Start at 500, same refill
- Pros: broke sooner, more tension.

### C. Never refill
- Cons: dead end, John would have to delete the save file by hand.

## Recommendation
Option A.

## What John would have to do or accept
A free refill, not an achievement. A "times broke" counter is possible later if wanted.
