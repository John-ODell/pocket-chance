# DR-035: Ultimate Texas Hold'em: AI players at the table

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-05
- **Blocks:** Hold'em screen (seat strips)
- **Needs HW review:** yes

## The decision
Whether the table shows other players, how many, how they decide, and how they are drawn. They play against the house only; nothing they do changes the player's cards, odds or payouts.

## Why it matters
John wants the WSOP-table feeling. Each seat costs drawing time on every phase and a little RAM, and the decisions cost evaluator time between phases.

## Options
### A. Two to four cosmetic seats with a fixed simple-strategy bot, text strips only (recommended)
- **What a seat is:** a name (from a short fixed list), a chip count that starts at 1000 and moves with its results (saved nowhere; it resets when the game is entered), two hole cards it never shows except as a hand name at showdown ("Ann: pair of 9s"), and a status line per phase ("check", "raise 4x", "fold", "WIN +40", "LOSE").
- **How it decides:** the same simple strategy as the help screen (DR-033), using `lib/poker.py` on its two cards plus the community cards: about 21 five-card evaluations per decision, roughly 15 to 25 ms on this board per seat per phase (estimate; the expert should measure), run between phases while the next cards are turned, never during an animation.
- **Cards:** each seat is dealt two real cards from the same deck (so the deck is shared, as at a real table), which slightly changes which cards the player and dealer receive but **not the odds**: every card is equally likely wherever it is dealt. Seats never affect the player's result.
- **Drawing:** a seat is a 60 x 56 strip of three size-1 lines (DR-034). Four strips are about 12 short strings, roughly 4 ms. Updating one strip is a band push.
- **RAM:** per seat two card ints, a chip count, a status string, a name: under 100 bytes; four seats plus the name list under 1 KB. Decisions reuse the evaluator already loaded for the player.
- **On today's RP2040:** this is all it should do. **With more RAM later** (or a bigger screen): show the seats' cards face up at showdown as real card art, more seats, animated chips. None of that fits 240 x 240 with nine cards already on screen.
- **Number of seats:** John asked for 3 to 5; the layout has room for **four** strips (two per side row). Four is the recommendation; the count is a parameter (0 to 4) in the settings so John can turn them off.
- Cons: the strips are text, not avatars; a fifth seat does not fit.

### B. No AI seats
- Pros: simplest, 4 ms faster per redraw, the hand-name lines get the side boxes.
- Cons: John asked for the table feeling.

### C. Seats with visible cards
- Cons: no screen space (eight more 40 x 56 cards would be needed); not possible at this size.

## Recommendation
Option A with four seats, switchable to zero. **Caribbean Stud retrofit:** yes, as a later request once Hold'em proves the strips: Stud's dealer and player rows are full (five cards each), so Stud seats would need a different placement (a 16 px strip under the top band, names and results only), which is its own layout decision.

## What John would have to do or accept
Other players appear as small text boxes with a name, chips and what they did; their cards are never shown. They do not change his odds.

## Appendix
Names list (fixed, fictional): Ann, Bo, Cy, Dee, Eli, Flo. Bots use `tools/uth_edge.py`'s strategy functions, moved into the engine.
