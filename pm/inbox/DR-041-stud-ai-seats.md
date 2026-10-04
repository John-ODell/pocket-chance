# DR-041: Caribbean Stud: other players as chip stacks

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-05
- **Blocks:** Nothing (Stud is built and awaits John's play-test); this adds to it
- **Needs HW review:** yes. Done: HR-041, **fits**. Measured: five seats decide in 5.3 ms total; the rail draws and pushes in 3.1 ms; 496 bytes of state. (Revision note 2026-10-05: numbers added, design unchanged.)

## The decision
Whether Caribbean Stud shows three to five other players as **chip stacks only** (no faces, no names, no cards), each playing the house with the same cards and dealer as the player, so that between rounds John can see who won and who lost; and where on the screen, how their results are produced, and whether their chips persist.

## Why it matters
John wants the table feeling from WSOP. Stud's screen is full (two rows of five cards), so the stacks must fit in the 12 px that are left, and every extra drawn pixel costs time on the result redraw. The seats must never change the player's odds, and their results must be honest.

## Options
### A. A chip rail at the bottom edge, five seats, real cards and basic strategy (recommended)
- **Where:** a 12 px rail at **y 228 to 239** under the prompt lines, inside the bottom band (168 to 239), so it is drawn and pushed with the result and prompts. Five seats of 44 px at x 10, 54, 98, 142, 186. Each seat is a code-drawn stack: up to six 2 px horizontal chip lines (one line per 200 chips, so 1000 chips is five lines), in a fixed colour per seat, with a **green up or red down 4 x 4 marker** at the left of the stack after each hand, cleared at the next deal. The player's own chips are the `$` figure as today.
- **How a seat plays:** each seat is dealt five real cards from the same deck after the player and dealer (10 + 25 = 35 of 52 cards), and plays the published basic strategy from `stud_rules.advice()` against the same dealer hand. So if the dealer turns over a flush, every seat that raised loses, as at a real table; the player's cards, dealer's cards and odds are exactly what they are without seats, because every card is equally likely wherever it is dealt. Cost: five hand evaluations plus the advice per hand, well under 10 ms, run once when the dealer's cards are revealed, before the result redraw. Nothing is random beyond the deck.
- **Chips:** each seat starts at 1000 when Stud is entered and moves by its real results; **not saved** (cosmetic; saving them would add fields to `/save.json` for no gameplay value). A seat that goes broke refills to 1000 silently.
- **Cost:** drawing the rail is about 30 small `fill_rect`s, roughly 1 ms, inside the bottom band that is already redrawn; RAM per seat under 50 bytes plus about 1 KB of code. The expert should measure the result redraw with the rail, and the engine time for five seats.
- Cons: at 12 px the stacks are small; the marker, not the height, is what the eye reads.

### B. A statistical result per seat (coin weighted to the real odds, no cards)
- Pros: no cards dealt, no evaluations.
- Cons: fake; seats would win against a dealer royal flush. Rejected on honesty.

### C. Replace the two prompt lines with a taller 24 px seat strip on the result screen only
- Pros: bigger stacks with the 24 x 24 chip art.
- Cons: the stacks vanish while betting, which is exactly when John wants to see them.

### D. No seats on Stud
- Pros: nothing to draw.

## Recommendation
Option A, five seats, the count a setting 0 to 5. **Blackjack later:** the same rail fits blackjack's bottom band (the prompt lines end at y 226 there too), with seats playing basic strategy against the same dealer up-card; a later request once Stud's rail is seen on the board.

## What John would have to do or accept
Five small coloured stacks along the bottom edge with a green or red marker after each hand. They are not saved; they start at 1000 each time Stud is opened. They do not change his odds.
