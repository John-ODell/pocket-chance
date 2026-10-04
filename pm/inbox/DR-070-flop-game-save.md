# DR-070: The flop game: when the bankroll is saved

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-06
- **Blocks:** The flop game's screen
- **Needs HW review:** no

## The decision
When `/save.json` is written and whether the armed multiplier (DR-064) survives leaving the game.

## Options
### A. Once per hand after the result is drawn, folds included; seats and the armed multiplier are not saved (recommended)
- Same file, format and order as the other games (DR-007, DR-030, DR-048). An armed multiplier is lost when John leaves the game; it is a table state, not his money.

### B. Save the armed multiplier
- Cons: a new field and a format version for a flag that lasts one hand.

## Recommendation
Option A.

## What John would have to do or accept
Leave the game with a multiplier armed and it is gone.
