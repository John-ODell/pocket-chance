# DR-065: A different table colour per game

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-06
- **Blocks:** Nothing
- **Needs HW review:** no (a different fill colour costs nothing)

## The decision
John asked for the new flop game to look like Ultimate "but with different background schemes". Which colour scheme does each game get?

## Options
### A. One felt colour per game, code-drawn, with the same gold and cream accents (recommended)
- Blackjack green (today's `rgb(0, 90, 40)`), Ultimate deep blue (`rgb(20, 40, 110)`), the new flop game burgundy (`rgb(110, 20, 30)`), Baccarat dark teal (`rgb(0, 80, 80)`), Caribbean Stud, if kept, stays green with a darker edge. Text colours are already chosen for a dark felt, so nothing else changes; the text-bounds test stays valid.
- Where a `table.565` image exists it still wins over the colour (DR-005); John can paint a per-game table later (`table_<game>.565`) as a separate request.
- Cost: one constant per game.

### B. A painted 240 x 240 table per game
- Cons: four 115 KB images to draw and stream; every scene change reads 21 to 26 ms from flash. Fine later, not needed to distinguish the games.

### C. All games the same green
- Cons: John has asked for a difference.

## Recommendation
Option A; John can pick other colours in the ruling.

## What John would have to do or accept
Nothing to draw. Name the colours if he dislikes mine.
