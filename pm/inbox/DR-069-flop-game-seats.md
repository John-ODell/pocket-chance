# DR-069: The flop game: the other players

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-06
- **Blocks:** Nothing (the game plays with 0 seats); DR-064 needs them for the multiplier
- **Needs HW review:** no (Ultimate's seats, measured in HR-044: four seats decide in 29 ms, showdown 134 ms)

## The decision
Whether the flop game has Ultimate's four chip-stack seats and how they play.

## Options
### A. Ultimate's four seats, each with two real cards from the same deck, playing the same simple strategy as the help screen; chips never saved (recommended)
- Each seat decides at the flop with the taught strategy (DR-071): fold, low or high. They settle against the same dealer hand with the same pays. Green or red marker, stacks growing or shrinking by a line per 200 chips, as in Ultimate (DR-044 rev).
- They never touch the player's cards or result; the test that proves the player's balance is identical with 0 and 4 seats carries over.
- They are also the "players" John's multiplier counts (DR-064): the multiplier is armed only when every seat and the player beat the dealer.
- Cost: `holdem_seats.py` reused with a new decision function; the showdown evaluates up to six seven-card hands (134 ms measured), run before the first flip as today.

### B. No seats
- Cons: John asked for them, and the multiplier rule needs other players.

## Recommendation
Option A. `FLOP_SEATS` in `pocket.py`, 0 to 4.

## What John would have to do or accept
Four chip stacks beside the cards, honest, never affecting his odds.
