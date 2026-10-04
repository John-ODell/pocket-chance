# DR-060: Baccarat: a result history strip

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-06
- **Blocks:** Nothing (an addition to the DR-052 layout)
- **Needs HW review:** no (12 small squares inside a band that is already pushed)

## The decision
Whether the screen shows the last results as a row of coloured marks, the "bead plate" every baccarat table displays.

## Why it matters
Baccarat players watch the run of results and bet on streaks. The scoreboard is part of the game's look, even though it changes no odds. It is also the only thing in the bottom band not yet claimed by DR-052 and DR-055.

## Options
### A. Twelve 8 x 8 squares at rows 214 to 222, oldest on the left: blue Player, red Banker, green Tie (recommended)
- x from 8 in steps of 18 (ends at x 214); newest result on the right; the row scrolls left when full.
- 12 bytes of state, about 1 ms to draw, included in the bottom band push after each coup. Not saved; starts empty on entry (DR-056).
- The legend is on the help screen in one line if John wants it; the three colours match the bet boxes' labels.
- Pros: the look of the real table for almost nothing.
- Cons: the bottom band holds the bet boxes, the prompt, this strip and the rail; the text test will check nothing overlaps.

### B. No history
- Pros: a calmer bottom band.
- Cons: the game looks less like baccarat than it could for 1 ms a coup.

### C. A full "big road" grid (columns per streak)
- Cons: needs 60 to 90 px of height; there is none.

## Recommendation
Option A.

## What John would have to do or accept
A row of small coloured squares showing the last twelve results. It is decoration: streaks do not change the odds, and the help screen does not pretend they do.
