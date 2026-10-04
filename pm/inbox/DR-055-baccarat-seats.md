# DR-055: Baccarat: the chip-stack seats

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-06
- **Blocks:** Nothing (the game plays without seats)
- **Needs HW review:** no (the rail is Stud's, measured in HR-041; the seats do no card work)

## The decision
Whether baccarat has the other-player chip stacks, where they sit and which side each one bets.

## Why it matters
At a baccarat table every player bets on the same two hands, so the seats cannot have their own cards: their only honest behaviour is to pick a side each coup and win or lose on the coup the player sees.

## Options
### A. Stud's five-seat rail, each seat betting 20 a coup on a side chosen by a fixed habit (recommended)
- Five stacks along rows 228 to 239 exactly as in Caribbean Stud (DR-041): a line per 200 chips, a green or red marker after each coup, grey when the seat's side ties.
- Each seat stakes 20 on the side its habit picks: seat 1 always Banker; seat 2 always Player; seat 3 follows the last winner (Banker on the first coup); seat 4 bets against the last winner; seat 5 bets Banker but Tie every fifth coup. The habits are cosmetic and make the rail move differently from the player's own result.
- Honest: the seats win or lose on the very coup on the screen, with the same pays and the same commission rounding (DR-059). They never touch the shoe or the player's result. Their chips start at 1000 whenever the game is entered and are never saved (DR-056).
- Cost: under 100 bytes of state, no card evaluation, under 1 ms per coup; the rail draw is 1.75 ms with a 12-row push (HR-041). `BAC_SEATS` in `pocket.py` sets 0 to 5 like `STUD_SEATS`.
- Cons: a seat's "decision" is a habit, not strategy; there is no good strategy in baccarat to give them.

### B. No seats in baccarat
- Pros: simpler bottom band.
- Cons: the other two table games have them and John asked for them; the rail is the cheapest the seats have ever been.

### C. Seats shown as side boxes with names and their side, as Hold'em's
- Cons: there is no room beside two three-card hands at 40 x 56 (DR-052).

## Recommendation
Option A. The test that proves the player's cards and results are identical with and without seats carries over from Stud.

## What John would have to do or accept
Five chip stacks along the bottom, each with its own betting habit, winning and losing on the same cards he sees.
