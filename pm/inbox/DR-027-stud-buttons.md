# DR-027: Caribbean Stud: button mapping

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-05
- **Blocks:** Caribbean Stud screen
- **Needs HW review:** no

## The decision
Which button does what in each phase.

## Options
### A. Same pattern as blackjack (recommended)
- Betting: joystick UP/DOWN ante ±5, LEFT/RIGHT ±25, **A** deal, **X** paytable and strategy screen, **B** menu.
- Decision (your five cards up, dealer's one card up): **A raise** (twice the ante), **B fold**, **X** paytable. Y does nothing.
- Result: **A** next hand (back to betting with the same ante), **B** menu, **X** paytable.
- Broke: **A** take 1000, **B** menu.
- Pros: A is always "go on", B is always "back/out", as in blackjack; folding with B feels natural ("back out of the hand").
- Cons: B both folds and leaves to the menu, in different phases; the prompt line always says which.

### B. A fold / B raise
- Cons: A would mean "give up", against the rest of the device.

## Recommendation
Option A.

## What John would have to do or accept
Nothing.
