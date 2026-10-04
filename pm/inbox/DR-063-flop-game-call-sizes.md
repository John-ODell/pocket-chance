# DR-063: The flop game: the low and high call, and what it does to the house edge

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-06
- **Blocks:** The flop game's engine (with DR-062)
- **Needs HW review:** no

## The decision
John wants to "bet low, high or fold" after the first three table cards. The published game has one call size (2x the Ante). Choosing between two sizes is worth several points to the player, so the sizes and what pays for them must be ruled together.

## Why it matters
Every extra choice is the player's: with two sizes he calls small on marginal hands and big on strong ones. Measured with `tools/casino_holdem_edge.py` (200,000 hands per row, simple strategy, noise about plus or minus 1 point of the Ante):

| Call rule | Ante vs an unqualified dealer | House edge, simple strategy |
|---|---|---|
| Fixed 2x (the published game) | paid by the table | **7.6%** (published 2.16% with optimal play) |
| Fixed 1x | table | 3.9% |
| Low 1x / high 2x | table | 1.3% |
| Low 2x / high 4x | table | **about 0** (−0.9 to +1.0 across runs) |
| Low 2x / high 3x | table | 4.0% |
| Low 1x / high 3x | table | −3.5% (player ahead) |
| Low 2x / high 4x, dealer needs a pair of **eights** | table | 11.0% |
| Low 2x / high 4x | **paid 1:1 only** | **0 to 2%** (two runs: 2.0, 0.0) |
| Low 1x / high 2x | paid 1:1 only | 1.9% |

The simple strategy loses about 5 points to optimal play in the published game, so any row near zero is a game an expert would play at a small advantage.

## Options
### A. Fixed 2x call, as published
- Pros: a known 2.16% optimal edge; the only version with a published figure.
- Cons: not what John asked for.

### B. Low 2x / high 4x, Ante table paid against an unqualified dealer
- John's rule, nothing else changed. About break-even with the taught strategy; player-favourable with expert play.

### C. Low 2x / high 4x, and against an unqualified dealer the Ante pays 1:1 instead of the table (recommended)
- John's rule, funded by the one change a player hardly notices: the bonus table applies only when the dealer has a hand and loses. About 0 to 2% with the taught strategy.
- Cons: still near break-even for an expert; the device holds no real money, so the "house" is John's own saved bankroll drifting slowly rather than quickly.

### D. Low 2x / high 4x, dealer qualifies with a pair of eights
- Pros: a real edge, about 11% simple, perhaps 5% optimal.
- Cons: the call pushes far more often, which feels like the game refusing to pay; and "4s or better" is the rule John named.

### E. Low 1x / high 2x
- Smaller swings; about 1.3% simple, player-favourable optimal. Hands cost at most 3 Antes.

## Recommendation
Option C. It is John's game with the house roughly level with the taught strategy. What would change my mind: if John wants the house to win over time the way the other three games do, pick A (published) or D (eights). DR-064's multiplier comes on top of this and gives the player a further 1.5 to 11 points depending on its cap.

## What John would have to do or accept
With his low/high rule the house edge is close to zero at the strategy the help screen teaches; a careful player can come out slightly ahead. If he wants the house to keep its edge, the price is one of the stiffer options.
