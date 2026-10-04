# DR-051: Baccarat: rules, payouts and house edge

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-06
- **Blocks:** The baccarat engine (John picked baccarat as the fourth game, 2026-10-06)
- **Needs HW review:** no

## The decision
The rules of punto banco baccarat as this device plays it, and the pays for the Player, Banker and Tie bets.

## Why it matters
Baccarat has no decisions after the bet, so the rules and pays alone set the house edge. The pays also decide whether the Banker bet needs a commission, which is awkward with whole chips (DR-059).

## Options
### A. Standard punto banco, eight decks, 5% commission, Tie 8:1 (recommended)
- **Bets:** one of Player, Banker or Tie per coup (DR-053 for how it is chosen).
- **Cards:** aces 1, twos to nines face value, tens and faces 0; only the last digit of a total counts. Two cards each, Player first. A natural 8 or 9 on either side ends the hand.
- **Third card:** the Player draws on 0 to 5 and stands on 6 and 7. If the Player stood, the Banker draws on 0 to 5 and stands on 6 and 7. If the Player drew a third card of value v, the Banker draws on 0 to 2; on 3 unless v is 8; on 4 when v is 2 to 7; on 5 when v is 4 to 7; on 6 when v is 6 or 7; and stands on 7. These are the standard tableau rules, the same in every casino.
- **Result:** the higher total wins. **Player pays 1:1. Banker pays 1:1 less a 5% commission** (19 for 20). **Tie pays 8:1.** A tie pushes the Player and Banker bets.
- **Shoe:** eight decks, reshuffled when the cut card is reached, 14 cards from the end, after the coup in play finishes (our `Shoe` with a penetration of 402 of 416 cards; "Shuffling..." between coups as in blackjack).
- **Measured** (`tools/baccarat_edge.py`, exact enumeration over a full eight-deck shoe, confirmed by 8 million coups on the real `Shoe` with the cut card): **Banker 1.06%, Player 1.24%, Tie 14.36%**, identical to the published figures.
- Cons: the 5% commission on whole chips does not divide at small stakes; DR-059 decides how to round.

### B. As A but Tie pays 9:1
- Measured **Tie 4.84%** (published 4.84%). Generous by casino standards; some tables offer it.
- Cons: nothing against it on this device except that 8:1 is what John will have seen in casinos and apps.

### C. "No commission" baccarat: Banker pays 1:1, except a Banker win with a total of 6 pays 1:2
- Measured **Banker 1.46%** (published 1.46%). Avoids the commission.
- Cons: the half pay on a six is a surprise to players who do not know the variant, and it still leaves a half chip at a stake of 5 (DR-059 applies either way).

### D. Fewer decks (six or one)
- Cons: changes the edges by hundredths of a point and nothing else; eight is the standard and what the published figures assume.

## Recommendation
Option A. It is the game everyone knows, every number matches the reference, and the help screen (DR-058) can quote the published edges. Option B (Tie 9:1) would change my mind only if John wants the Tie to be a reasonable bet rather than the long shot it usually is; it is a one-number change.

## What John would have to do or accept
Betting Banker loses about 1 chip per 100 staked over time, Player about 1.2, Tie about 14. Nothing to draw. The Banker commission rounds to whole chips as DR-059 decides.

## Appendix
`python3 tools/baccarat_edge.py`. Reference: https://wizardofodds.com/games/baccarat/ (rules and figures checked 2026-10-06). Exact results: Player 1.235%, Banker 1.058%, Banker no-commission 1.458%, Tie 8:1 14.360%, Tie 9:1 4.844%; naturals end 34.3% of coups; outcome frequencies Banker 45.86%, Player 44.62%, Tie 9.52%. Monte Carlo on `lib/cards.Shoe` with the cut card: 1.240 / 1.053 / 1.461 / 14.384 / 4.872%.
