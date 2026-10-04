# DR-066: The flop game: screen layout and how the cards turn

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-06
- **Blocks:** The flop game's screen (DR-062)
- **Needs HW review:** yes (reuses Ultimate's measured redraw and band pushes, but the flop turns three cards at once in a new order)

## The decision
Where the player's two cards, the dealer's two, the five table cards, the seats and the prompt sit, and how the cards turn.

## Options
### A. Ultimate's layout as is, with the reveal order of the new rules (recommended)
- Rows: top band 0 to 23 (chips, Ante, bet); dealer's pair 24 to 83 at x 76 and 120; five table cards 84 to 143 at x 12, 56, 100, 144, 188; player's pair 144 to 203 at x 76 and 120; bottom band 204 to 239 with three text lines, exactly as `games/holdem.py` (DR-043). Four seat boxes at x 8 and 172 beside the pairs (DR-044).
- Deal: the player's two cards face up, the dealer's two face down, the five table cards face down (one redraw, 73 ms measured for Ultimate). Then **the first three table cards turn together** after 300 ms (one band push, 27 ms). The prompt asks for the call (DR-067). On a call, the last two table cards turn together, then the dealer's cards one by one 300 ms apart, then the result; on a fold the dealer's cards turn anyway so John sees what he missed, then the result.
- Felt colour per DR-065.
- Pros: nothing new for the expert to measure except the order; every element is on the board today.

### B. Dealer's cards turn before the last two table cards
- Cons: in the real game the dealer shows last; the suspense is the turn and river.

## Recommendation
Option A.

## What John would have to do or accept
The screen looks like Ultimate with a different felt; the first three table cards turn before his decision, the last two after it.
