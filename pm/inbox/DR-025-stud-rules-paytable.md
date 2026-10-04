# DR-025: Caribbean Stud: rules, raise paytable and house edge

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-05
- **Blocks:** The Caribbean Stud engine (the evaluator in lib/poker.py is built)
- **Needs HW review:** no

## The decision
The rules of Caribbean Stud as this device plays it, and the raise paytable, which together set the house edge.

## Why it matters
This is the house edge of the game. The figures below are measured with a simulator built on our own hand evaluator (`tools/stud_edge.py`, 1.5 million hands per line) and agree with the published reference (Wizard of Odds: 5.224% of the ante with optimal play).

## Options
### A. Standard rules and the standard paytable (recommended)
- **Play:** the player posts an **ante**; player and dealer get five cards; the dealer shows one card. The player **folds** (loses the ante) or **raises exactly twice the ante**. The dealer **qualifies with ace-king or better** (lowest qualifier A-K-4-3-2). If the dealer does not qualify, the ante pays 1:1 and the raise is returned. If the dealer qualifies and the player's hand is higher, the ante pays 1:1 and the raise pays by the table below. If the dealer qualifies and wins, the player loses both. Ties push both.
- **Raise paytable:** pair or less 1:1, two pair 2:1, three of a kind 3:1, straight 4:1, flush 5:1, full house 7:1, four of a kind 20:1, straight flush 50:1, royal flush 100:1.
- **No progressive jackpot** side bet in version 1 (it needs its own saved pot and rules; it is the worst bet on the table at 26% house edge).
- **House edge:** with the published basic strategy **5.21% of the ante** (2.55% of all chips staked, because the raise is only placed on half the hands); with the simplest strategy a player is likely to use ("raise with a pair or ace-king, fold below") **5.63%** of the ante. The player folds about 48% of hands.

### B. Standard rules, lower pays (e.g. two pair 1:1)
- Cons: raises the edge for no reason; this is a toy.

### C. Dealer qualifies with any pair instead of A-K
- Cons: changes the odds away from the published game; our tool would have to re-derive the edge and there is no reference to check it against.

## Recommendation
Option A. Everything is a parameter in the engine (qualifier, paytable) so a later change is one line.

## What John would have to do or accept
House edge about 5.2% of the ante with good play (fold below ace-king, raise with a pair or better, and with ace-king follow the three published rules which the paytable screen will show in plain words). That is far higher than blackjack's 0.55%: a 5-chip ante loses about a quarter of a chip per hand on average.

## Appendix
`python3 tools/stud_edge.py` prints both strategies. Reference: https://wizardofodds.com/games/caribbean-stud-poker/ . Basic strategy for ace-king (Wizard): raise if the dealer's up-card is 2 to queen and matches one of your cards; raise if the up-card is ace or king and you hold a queen or jack; raise if the up-card matches none of your cards, you hold a queen and the up-card is lower than your fourth-highest card; otherwise fold.
