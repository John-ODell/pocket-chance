# DR-071: The flop game: the help screen

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-06
- **Blocks:** Nothing
- **Needs HW review:** no (same shape as `holdem_pay`, 215 ms measured)

## The decision
What X shows: the Ante table, the dealer rule, the call strategy and the multiplier rule.

## Options
### A. One screen (recommended)
Proposed text at 29 characters per line or fewer, assuming DR-063 option C and DR-064 option B; the figures change with the rulings:

```
Casino Hold'em
Ante: royal 100  str flush 20
quads 10  full 3  flush 2
else 1:1. Dealer needs a pair
of 4s or better; if not, Ante
pays 1:1 and the call pushes.

HIGH 4x: pair using your card
or better; four to a flush or
a straight using your card.
LOW 2x: an ace, or your card
beats the board. Else FOLD.

If everyone beats the dealer,
the next hand's call pays x2.
Edge about 0-2% of the Ante
any key: back
```
- The strategy is the one the simulator measured and the seats play (DR-069), so John and the seats are on equal terms.

### B. Pays only
- Cons: the fold rule is the whole skill of the game.

## Recommendation
Option A.

## What John would have to do or accept
Nothing. Wording can change in the ruling.
