# DR-036: Ultimate Texas Hold'em: button mapping

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-05
- **Blocks:** Hold'em screen
- **Needs HW review:** no

## The decision
Which button does what in each phase.

## Options
### A. A = the raise on offer, B = check (or fold at the river), X = help, Y = 3x pre-flop (recommended)
- Betting: joystick UP/DOWN Ante ±5, LEFT/RIGHT ±25 (Blind always equals the Ante), **A** deal, **X** pays and strategy, **B** menu.
- Pre-flop: **A raise 4x**, **Y raise 3x**, **B check**.
- Flop: **A raise 2x**, **B check**.
- River: **A raise 1x**, **B fold**.
- Result: **A** next hand, **B** menu. Broke: **A** take 1000, **B** menu.
- The prompt line always names the two or three live buttons with their amounts ("A raise 40   Y 30   B check").
- Pros: A is always "bet more", B "no bet / out", as in blackjack and Stud.
- Cons: B means check in two phases and fold in one; the prompt says which.

### B. Hide the 3x raise (A 4x, B check only)
- Pros: one fewer button; 3x is never the better play.
- Cons: John described 4x and 3x as what WSOP offers.

## Recommendation
Option A; the help screen says plainly that 4x is always the better raise.

## What John would have to do or accept
Nothing.
