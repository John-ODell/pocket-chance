# DR-053: Baccarat: buttons

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-06
- **Blocks:** The baccarat screen
- **Needs HW review:** no

## The decision
How the player chooses the side, sets the stake, deals, repeats a bet and opens the paytable.

## Options
### A. Joystick left/right picks the side, up/down the stake; A deals; the bet stays for the next coup; X pays; B menu (recommended)
- **Left/right** moves the gold frame across PLAYER, TIE, BANKER (DR-052). **Up/down** changes the stake in steps of 5 (DR-054), as in every other game.
- **A** deals the coup. After the result, **A deals again with the same side and stake**, which is the "repeat bet" every baccarat player expects; moving the joystick first changes either.
- **X** shows the help screen (DR-058) between coups. **B** returns to the menu between coups.
- Nothing is pressed during a coup: the cards follow the tableau rules on their own (DR-051).
- Pros: one bet of one amount per coup keeps the top band's "$chips  bet" meaning unchanged; no new input idea beyond left/right, which the menu already uses.
- Cons: cannot bet two sides at once (for example Banker and Tie together). I do not recommend that: it needs a second stake display and makes the top band's bet figure ambiguous.

### B. Y cycles the side; the joystick only sets the stake
- Pros: one more free joystick axis.
- Cons: three boxes in a row beg for left/right; cycling is slower and Y has no other job here.

### C. Dedicated keys: A Player, Y Tie, X Banker, deal automatically after a choice
- Pros: one press per coup.
- Cons: loses the help key; an accidental press deals a coup.

## Recommendation
Option A.

## What John would have to do or accept
Left/right to pick a side, up/down for the stake, A to deal, A again to repeat.
