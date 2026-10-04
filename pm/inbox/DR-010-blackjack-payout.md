# DR-010: Blackjack payout: 3:2 or 6:5

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-03
- **Blocks:** Nothing, parameter in the rules engine (`bj_num`, `bj_den`, default 3:2)
- **Needs HW review:** no

## The decision
How much a natural blackjack (Ace + ten-value card on the first two cards) pays.

## Why it matters
6:5 is a big hidden cost to the player.

## Options
### A. 3:2 (recommended)
- Bet 10, win 15.
- House edge (6 decks, S17, no splitting): about 0.95%. RTP about 99.05%.

### B. 6:5
- Bet 10, win 12.
- House edge (same rules): about 2.39%. RTP about 97.6%. It costs the player about 1.4 points more.

## Recommendation
Option A. Rounding: winnings are whole chips and round down. A blackjack on a bet of 5 pays 7, not 7.5, which costs the player half a chip on odd bets. Say if you would prefer rounding up.

## What John would have to do or accept
Nothing.

## Appendix
Measured in `tools/bj_edge.py`. See DR-009 for the method and caveats.
