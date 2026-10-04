# DR-019: Slots: bet sizes and the shared bankroll

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-04
- **Blocks:** Slots screen
- **Needs HW review:** no

## The decision
How much a spin costs and whether slots share the blackjack bankroll and chip art.

## Options
### A. Same bankroll, same chips, bet 5 to 100 per spin in steps of 5 (recommended)
- One `$` balance for the whole device (already saved in `/save.json`); UP/DOWN change the bet by 5, LEFT/RIGHT by 25; A spins; the same chip images show the bet.
- Max 100 keeps the jackpot at 100,000 chips (the `$` line fits 7 digits) and keeps a losing streak survivable with the 1000-chip start.
- Pros: one wallet to understand; nothing new to draw; broke and refill work exactly as in blackjack (DR-013).
- Cons: none I see.

### B. Separate slots credits
- Cons: two balances to explain and save; no gain.

### C. Bet 5 to 500 like blackjack
- Cons: a 500-chip spin at 6% edge burns the 1000 start in a few minutes of bad luck; the jackpot would be 500,000 and overflow the top line.

## Recommendation
Option A. The RTP does not depend on bet size.

## What John would have to do or accept
Slots and blackjack draw from the same chips.
