# DR-043: Ultimate Texas Hold'em: screen layout for nine cards and seat strips

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-05
- **Blocks:** Hold'em screen
- **Needs HW review:** yes. Done: HR-043, **fits with limits**. Measured: full redraw with nine face-up cards and four seat boxes **85 ms code-drawn, 74 ms from a sheet** (my 60/55 estimate was low); community band push 27 ms. Limits: card backs code-drawn always, full redraw only at phase changes, size-1 text only. (Revision note 2026-10-05: numbers added, layout unchanged.)

## The decision
Where the dealer's two cards, the five community cards, the player's two cards, the hand names, the bets and the prompts go, and where seat strips for AI players (DR-044) would sit.

## Why it matters
Nine 40 x 56 cards in three rows is 168 px of the 240; only 48 px are left for everything else. The redraw cost must stay near blackjack's (45 ms full redraw; a card is 3.9 ms code-drawn, 3.4 ms from a sheet).

## Options
### A. Three card rows, two of them with side strips, a 36 px bottom band (recommended)
```
  y   0-23   $chips (size 2) | ante 10  blind 10  play 40 (size 1)
  y  24-83   [seat 1]  [D][D]  [seat 2]    dealer's two cards at x 76 and 120, face down until showdown
  y  84-143  [C][C][C][C][C]               community cards at x 12/56/100/144/188, face down until dealt
  y 144-203  [seat 3]  [P][P]  [seat 4]    player's two cards at x 76 and 120
  y 204-239  result/hand line 206, prompts 218 and 228 (all size 1); a 160 x 32 banner fits at y 204-236
```
- Seat strips are 60 x 56 boxes at x 8-68 and 172-232 in the dealer and player rows: three size-1 lines each (name, chips, status such as "raise 4x", "fold", "WIN +40"). Without AI seats those boxes hold the hand names instead: "Dealer: pair of 9s" split over two lines on the left of the dealer row, "You: two pair" on the left of the player row.
- Redraw: full redraw only when cards are turned (deal, flop, river, showdown) and at the result; bet changes and seat updates push their band (56 or 60 rows, about 15 ms). With all nine cards face up the full redraw is about 9 x 3.9 + 4 strips of text + show = roughly 60 ms code-drawn, 55 ms with a sheet (the expert should measure; the limit is the same as Stud's).
- Cons: the bottom band is 36 px, so the result line and two prompt lines are size 1 only; no size-2 text on this screen except the chips figure.

### B. Two rows: community cards in the middle, dealer and player cards side by side in one row
- Pros: frees a 56 px bottom band.
- Cons: four cards plus two seat strips do not fit in 240 px; seats would have to go.

### C. Smaller cards for Hold'em (32 x 44)
- Cons: a second card art size for John to draw, or a scaler on the board; rejected.

## Recommendation
Option A. The expert should measure: a full redraw with nine face-up cards and four seat strips, code-drawn and with a sheet; one seat-strip band push; RAM of the screen module compared with Stud's (~14 KB on import).

## What John would have to do or accept
Nothing new to draw. The Hold'em screen is denser than blackjack's and its text is small.
