# DR-011: Blackjack: number of decks and when to reshuffle

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-03
- **Blocks:** Nothing, parameters in the rules engine (`decks`, `penetration`)
- **Needs HW review:** no

## The decision
How many 52-card decks are in the shoe, and how much is dealt before reshuffling.

## Why it matters
Fewer decks help the player. With one deck and a late reshuffle, someone who counts cards can beat the game.

## Options
### A. 6 decks, reshuffle after 75% is dealt (recommended)
- House edge (S17, 3:2, no splitting): about 0.95%. RTP about 99.05%.
- Pros: the usual casino shoe. Counting is impractical. 312 cards held in a 312-byte array.
- Cons: none noticeable.

### B. 2 decks
- House edge: about 0.96% in my run, within noise of A.
- Pros: nothing over A.

### C. 1 deck
- House edge: about 0.58%.
- Cons: with a late reshuffle it can be counted, and the house edge shifts as cards are used.

## Recommendation
Option A. Penetration is also a parameter if John wants a different cut.

## What John would have to do or accept
A "Shuffling" moment on screen about every 35 hands.
