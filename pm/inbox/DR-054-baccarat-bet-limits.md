# DR-054: Baccarat: stake limits against the bankroll

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-06
- **Blocks:** The baccarat engine
- **Needs HW review:** no

## The decision
The stake range and when the game counts the player as broke.

## Options
### A. Stake 5 to 100 in steps of 5, capped at the balance; broke below 5 (recommended)
- Baccarat stakes the bet once; nothing is added during a coup, so the exposure is the stake itself and the cap is simply the balance.
- The most a coup can lose is 100; the most it can win is 800 (Tie 8:1 at 100), under the 1000 start.
- Broke means fewer than 5 chips; the free 1000 refill works as in the other games (DR-007).
- Pros: the same joystick feel and the same 5 to 100 range as Caribbean Stud.

### B. Stake 5 to 500 like blackjack
- Cons: a 500 Tie win is 4000 chips; with one-side betting and no decisions the swings would dwarf the other games.

### C. Different limits per side (for example Tie capped at 50)
- Cons: a casino caps Tie to limit its own exposure; this device has no such worry, and two caps complicate the joystick.

## Recommendation
Option A.

## What John would have to do or accept
Stakes of 5 to 100 on any side; a coup can never cost more than 100.
