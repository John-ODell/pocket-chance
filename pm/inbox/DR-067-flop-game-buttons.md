# DR-067: The flop game: buttons

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-06
- **Blocks:** The flop game's screen
- **Needs HW review:** no

## The decision
Which key does what at the one decision point: call low, call high or fold.

## Options
### A. A high, Y low, B fold; joystick Ante; X help; B menu between hands (recommended)
- Matches Ultimate's keys (DR-045): A is the big raise, Y the smaller one, B the way out. The prompt reads "A high 40   Y low 20   B fold" with the chip amounts filled in (DR-063 sets the sizes).
- Betting: joystick up/down sets the Ante, A deals, X shows the help screen, B returns to the menu. After the result, A deals the next hand.
- Pros: a player who knows Ultimate knows this game at once.

### B. Joystick left/right chooses low or high, A confirms, B folds
- Cons: two presses for a call; Ultimate uses single keys.

## Recommendation
Option A.

## What John would have to do or accept
A for the high call, Y for the low call, B to fold.
