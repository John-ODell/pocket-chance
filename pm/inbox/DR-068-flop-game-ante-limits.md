# DR-068: The flop game: Ante limits against the exposure

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-06
- **Blocks:** The flop game's engine
- **Needs HW review:** no

## The decision
The Ante range, given that a hand can cost the Ante plus the high call.

## Options
### A. Ante 5 to 50 in steps of 5, capped so the Ante plus the high call is always covered (recommended)
- With a high call of 4x the Ante (DR-063 option A) the exposure is 5 Antes: cap at a fifth of the bankroll, most a hand can lose 250 from the 1000 start. With a high call of 2x the exposure is 3 Antes and the cap a third, as in Caribbean Stud.
- Broke below 5 x the minimum Ante; the free 1000 refill as in every game (DR-007).
- Pros: the same rule as Ultimate (DR-046) and Stud (DR-028): the best call is always affordable when the cards are dealt.

### B. Ante 5 to 100
- Cons: a hand could cost 500, half the start.

## Recommendation
Option A.

## What John would have to do or accept
Antes of 5 to 50; a hand never costs more than 250.
