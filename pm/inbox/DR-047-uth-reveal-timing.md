# DR-047: Ultimate Texas Hold'em: how the cards are turned

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-05
- **Blocks:** Hold'em screen
- **Needs HW review:** yes

## The decision
The order and timing of turning the community cards and the dealer's cards.

## Options
### A. Phase cards turn together; the dealer's two cards turn one by one at showdown (recommended)
- Deal: the player's two cards face up, the dealer's two and five community cards face down (one full redraw).
- Flop: the three community cards turn together (community band push, about 15 ms) after the pre-flop decision, with a 300 ms pause before the prompt changes.
- Turn and river: the last two together (same band), after the flop decision.
- Showdown: the dealer's two cards turn one at a time 300 ms apart (dealer band pushes), then the result (full redraw), then the save, then buttons drained (the Stud pattern, HR-029: schedule by the clock, nothing between flips).
- AI seats update their status line with the phase they just acted in, in the same band push as the cards (DR-044).
- Cons: about 1.5 s of pauses across a hand.

### B. Every card one by one
- Cons: nine flips at 300 ms is 2.7 s of waiting per hand, too slow for a game that already has three decisions.

### C. Everything at once
- Cons: no sense of the hand unfolding.

## Recommendation
Option A. The expert should confirm the community-band push with five face-up cards.

## What John would have to do or accept
Short pauses as the table cards turn.
