# DR-030: Caribbean Stud: when the bankroll is saved

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-05
- **Blocks:** Caribbean Stud screen
- **Needs HW review:** no

## The decision
When the shared `/save.json` is written during a Caribbean Stud hand.

## Options
### A. Once per finished hand, after the result is drawn, including folded hands (recommended)
- Same file, format and backup rules as DR-007/DR-008; same order as blackjack and HR-021: result drawn and pushed first, then the save (54 to 151 ms), never during the reveal.
- A fold changes the balance, so it saves too. A hand takes 5 to 10 seconds, so this is well under one write per round of blackjack.

### B. Save only when leaving the game
- Cons: a power cut mid-session loses the session's wins and losses.

## Recommendation
Option A.

## What John would have to do or accept
Nothing.
