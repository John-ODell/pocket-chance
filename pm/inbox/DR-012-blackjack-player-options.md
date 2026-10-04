# DR-012: Blackjack player options in version 1: hit, stand, double only

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-03
- **Blocks:** Nothing, the engine already supports hit, stand and double (any two cards)
- **Needs HW review:** no

## The decision
Which actions the player gets in the first version of blackjack.

## Why it matters
Splitting pairs, insurance and surrender are extra screens, extra buttons and more rule choices. Leaving out splitting raises the house edge, because splitting is a player advantage.

## Options
### A. Hit, Stand, Double down on any first two cards (recommended)
- Pros: fits the four buttons and the available screen space; engine is built and tested.
- House edge (6 decks, S17, 3:2, basic strategy): about 0.95%. For comparison, commonly quoted casino figures for full rules with splitting are around 0.4% (from my memory, not measured here).

### B. Add splitting now
- Pros: closer to real blackjack.
- Cons: a second hand on a 240 px screen, more rule choices (re-splitting, aces), more testing.

### C. Add splitting, insurance and surrender
- Cons: the most work, and insurance is a bad bet that tempts new players.

## Recommendation
Option A, then splitting as its own request later if John wants it. No insurance or surrender, ever, unless asked.

## What John would have to do or accept
No splitting. The house edge is about 0.5 points higher than a full casino table.
