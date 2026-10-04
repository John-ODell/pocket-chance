# DR-035: Ultimate Texas Hold'em: AI players at the table

- **Status:** pending, **revision 2** (2026-10-05): John clarified that the other players are chip stacks only, no names, no cards, no hand names. The text-strip design is withdrawn; the seats are now stacks in the side boxes, matching DR-041 for Stud.
- **Filed by:** senior dev
- **Date:** 2026-10-05
- **Blocks:** Hold'em screen (seat strips)
- **Needs HW review:** yes

## The decision
Whether the table shows other players, how many, how they decide, and how they are drawn. They play against the house only; nothing they do changes the player's cards, odds or payouts.

## Why it matters
John wants the WSOP-table feeling. Each seat costs drawing time on every phase and a little RAM, and the decisions cost evaluator time between phases.

## Options
### A. Four chip stacks in the side boxes, real cards and the simple strategy (recommended)
- **What a seat is:** a stack of chips in one of the four 60 x 56 side boxes of the layout (DR-034, x 8 to 68 and 172 to 232 in the dealer and player rows): the 24 x 24 chip art (or a code-drawn disc) piled with a 4 px offset, one chip per 200 chips so 1000 is five chips, 44 px tall at most, with the count under it in size-1 text and a **green up or red down marker** after each hand, cleared at the next deal. No name, no cards, no hand name.
- **How it plays:** each seat gets two real cards from the same deck (player 2 + dealer 2 + 5 community + 4 x 2 = 17 of 52) and plays the simple strategy of the help screen (DR-033) using `lib/poker.py` at the same three decision points, against the same community and dealer cards. Cost: roughly 21 five-card evaluations per decision per seat, estimated 15 to 25 ms per seat per phase on this board (the expert should measure), run between phases before the next cards turn, never during a flip. The player's odds and results are untouched: every card is equally likely wherever it is dealt.
- **Chips:** start at 1000 on entering Hold'em, move by real results, refill silently when broke, **not saved** (DR-039).
- **Cost:** four stacks of up to six chip blits (sheet or disc, about 1 ms each) plus four short strings: under 30 ms worst case on a full redraw, pushed as part of the side rows; RAM under 100 bytes per seat.
- **On today's RP2040** this is the ceiling. **With more RAM or a bigger screen later:** the seats' cards face up at showdown, a fifth seat, animated chips.
- **Count:** four fit the layout (John asked for three to five); the count is a setting 0 to 4.

### B. A statistical result per seat (no cards, weighted coin)
- Cons: fake; rejected on honesty, as in DR-041.

### C. No seats
- Pros: faster redraw; the side boxes show the hand names instead.

## Recommendation
Option A with four seats. The Stud version (DR-041) comes first, as a 12 px rail, because Stud's rows are full; Hold'em has the room for proper stacks.

## What John would have to do or accept
Four stacks of chips at the sides of the table that grow or shrink each hand, with a green or red marker. No names or cards. They do not change his odds and start again at 1000 each time he opens Hold'em.

## Appendix
Bots use `tools/uth_edge.py`'s strategy functions, moved into the engine.
