# DR-064: The flop game: the WSOP "everyone beat the house" multiplier

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-06
- **Blocks:** Nothing (the game plays without it)
- **Needs HW review:** no (one flag and a banner line)

## The decision
John's rule from the WSOP app: when every player at the table beats the house, the next hand pays winners N times, N being the number of players at the table. Which version, if any, the device plays.

## Why it matters
Measured on top of DR-063 option C with four seats and the player (N = 5), `tools/casino_holdem_edge.py`, 200,000 hands per row:

| Version | How often it arms | House edge, simple strategy |
|---|---|---|
| None | | 0 to 2% |
| **As described:** x5 on the whole win, armed whenever everyone beats the dealer (an unqualified dealer counts as beaten) | 10.8% of hands | **−61%** (the player wins 61 chips per 100 Antes) |
| x5 on the call bet only, armed only when everyone beats a **qualified** dealer | 3.5% | −11% |
| x3 on the call only, qualified dealer | 3.5% | −4.6% |
| **x2 on the call only, qualified dealer** | 3.5% | **−1.5%** (about even, within noise) |

With an unqualified dealer counting as "beaten", the table beats the house one hand in nine; that is why the rule as described turns the game into a chip fountain.

## Options
### A. As described: N times the whole win, armed whenever everyone beats the dealer
- Pros: exactly the app's rule.
- Cons: the bankroll climbs forever (−61% of the Ante per hand); after a few sessions the chips number is meaningless and the other games' edges stop mattering.

### B. Armed only when everyone beats a qualified dealer; the next hand multiplies the call bet's win by 2 (recommended)
- Fires about every 28 hands, shown on the bottom line as "x2 NEXT HAND" in gold during the betting and on the prompt. Only the call bet's win is doubled, never the Ante table or a fold. The seats' calls are doubled too. The flag lasts one hand and is not saved (DR-070).
- The game stays roughly level overall with the taught strategy (−1.5%, within noise of zero).
- Cons: "x2" is less dramatic than "x5"; the arming condition needs a dealer hand, which is what makes it rare enough.

### C. As B but N uncapped (x5 with four seats)
- Cons: −11% with the taught strategy; the bankroll grows steadily.

### D. No multiplier
- Pros: the cleanest edge (DR-063).
- Cons: John called it the fun rule.

## Recommendation
Option B. If John would rather have the x5 excitement and accept a game he wins over time, pick C; if he wants a true house edge with the multiplier, pair it with DR-063 option D (dealer needs a pair of eights), which I would then re-measure.

## What John would have to do or accept
About once every 28 hands the screen announces the next hand's call pays double. Over time the game roughly breaks even for a player using the help-screen strategy.
