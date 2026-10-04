# DR-016: Add splitting pairs to blackjack

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-04
- **Blocks:** nothing. Blackjack v1 plays without it (DR-012). This adds a feature John asked for after playing.
- **Needs HW review:** yes, for the redraw cost of two hands in the player band and the RAM of a second hand. Measured baseline for the band it would reuse: hit/stand band 29 ms (hw/BUDGET.md, "First on-board code"). I believe it fits, since the band and the number of sprites per redraw are the same, but the expert should confirm.

## The decision
Whether the player may split a pair into two hands, and under which rules.

## Why it matters
John expected it when dealt a pair. Splitting is a player advantage: it lowers the house edge by about 0.4 points. It also needs a second hand on a 240 px screen and a fourth button, so the rules should be fixed before I build it.

## Measured house edge (tools/bj_split.py, 3 million hands each, 6 decks, S17, 3:2, basic strategy)
| Rules | House edge (of the initial bet) | RTP |
|---|---|---|
| A. No split (v1 as shipped) | **0.97%** | 99.0% |
| B. Split once, any pair, aces get one card each, double after split allowed | **0.55%** | 99.45% |
| B2. As B but no double after split | 0.63% | 99.4% |
| B3. As B but aces may not be split | 0.65% | 99.35% |
| C. Re-split up to 4 hands, double after split, no re-split of aces | 0.40% | 99.6% |

Noise about ±0.05 points. A casual player gets less than this; the figures assume correct splitting decisions.

## Options
### A. Keep v1: no splitting
- Pros: nothing to build.
- Cons: John has asked for it; the game feels incomplete to anyone who knows blackjack.

### B. Split once into two hands (recommended)
- What it is: when the first two cards are the same rank (ten-value cards must be the same rank, e.g. two kings, not king and jack), **Y** splits. The second bet equals the first and must be covered by the bankroll. Each hand gets one new card. Aces: one card each and both stand (no hitting split aces). Other hands play as normal, hit / stand / double. No re-splitting. A 21 after a split pays even money, not 3:2 (standard).
- Screen: the two hands sit side by side in the player band (each up to 4 cards at a 20 px overlap step = 100 px; two hands plus a 16 px gap = 216 px). The hand being played has a gold marker under it and its total; the other is dimmed. The dealer, bankroll and prompt areas do not move. Result shows both hands' outcome ("WIN / LOSE") and the combined net.
- Pros: the common rule set; keeps the 4 buttons mapped A hit, B stand, X double, Y split; two hands fit the screen readably.
- Cons: about a day of work (engine, tests, screen); more rules for the expert to time.
- Cost: RAM: a second list of a few bytes. Flash: a few KB of code. Redraw: the same 142-row band as a hit, with up to 8 card sprites instead of 5.

### C. Re-split up to four hands
- Pros: lowest edge.
- Cons: four hands cannot be drawn readably at 240 px (each would get 56 px, barely more than one card). Not worth it on this screen.

## Recommendation
Option B. It is what John expects, cuts the house edge from about 0.97% to about 0.55%, and fits the screen and buttons. I would pick B3 (no splitting aces) only if the expert finds two hands redraw too slowly, since aces are the most common split and the one most worth a second card draw animation; I do not expect that.

## What John would have to do or accept
A new button: **Y** splits when you are dealt a pair. The house edge drops to about 0.55% (RTP about 99.45%). Nothing to upload until it is built; it will arrive as new versions of `games/blackjack_rules.py`, `games/blackjack_table.py` and `games/blackjack.py` in `UPLOAD.md`.

## Appendix
Simulation detail: `tools/bj_split.py`. Pair strategy used: always split A,A and 8,8; 2,2/3,3/7,7 against dealer 2–7; 6,6 against 2–6; 9,9 against 2–6 and 8–9; 4,4 against 5–6 only when doubling after a split is allowed; never 5,5 or ten-value pairs. Edges are quoted against the initial bet, as casinos do; against all chips staked they are about 0.1 point lower (also printed by the tool). Previous figures in DR-009 to DR-012 used `tools/bj_edge.py`, which gave 0.95% for no-split; this tool gives 0.97% for the same rules, within noise.
