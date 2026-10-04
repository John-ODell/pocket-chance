# DR-039: Ultimate Texas Hold'em: when the bankroll is saved

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-05
- **Blocks:** Hold'em screen
- **Needs HW review:** no

## The decision
When `/save.json` is written during a Hold'em hand.

## Options
### A. Once per hand after the result is drawn, folds included; AI seats are never saved (recommended)
- Same file, format and order as blackjack and Stud (DR-007, DR-030, HR-021). Seat chip counts are cosmetic and reset when the game is entered, so nothing else is written.

### B. Save the AI seats too
- Cons: more fields in the save for no gameplay value; the format would need a version bump.

## Recommendation
Option A.

## What John would have to do or accept
The other players' chips start again at 1000 each time he opens Hold'em.
