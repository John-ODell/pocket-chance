# DR-042: Ultimate Texas Hold'em: rules, Blind paytable and house edge

- **Status:** pending, **revision 2** (2026-10-05): the simulator bug is found and fixed; the measured edge now agrees with the published figure.
- **Filed by:** senior dev
- **Date:** 2026-10-05
- **Blocks:** The Hold'em engine
- **Needs HW review:** no

## The decision
The rules of Ultimate Texas Hold'em as this device plays it, and the Blind paytable.

## Why it matters
This sets the house edge. Figures: the published reference (Wizard of Odds) is **2.185% of the Ante with optimal play** and **2.43% with the Wizard's "simple strategy"**. Our simulator (`tools/uth_edge.py`) currently measures the published simple strategy at about 6.9% of the Ante (1.6% of all chips staked, since the Play bet is large), which does not match the published 2.43%; see the next section. Raising 3x instead of 4x before the flop costs about 9 more points: always 4x.

## The help screen and the house edge (revision 2)
The simulator's earlier 6.9% came from a bug: a board pair with a better kicker counted as a "hidden pair" at the river, which triggered 1x raises on hopeless hands. Fixed (`tools/uth_edge.py`, 800,000 hands, 8 seeds): **the full published simple strategy measures 2.8% of the Ante** (0.7% of all chips staked, folds 18%), consistent with the published 2.43% within the run's noise of about half a point. **Without the river outs count** it measures **6.8%** (folds 28%). **Raising 3x instead of 4x** costs about 8 more points.

So the product decision for John stands and is now quantified: the help screen should teach the **full** simple strategy, including the river rule ("raise 1x if fewer than 21 of the unseen cards could give the dealer a hand that beats yours; otherwise fold"), because the version without it loses the Ante 2.5 times faster. Recommended: the game shows the dealer-outs count on the river prompt as a hint, since counting 45 cards in the head is not realistic; the cost is 45 seven-card evaluations once per hand, about 45 x 28 ms = 1.3 s on this board by HR-044's figure, which is too long for the 300 ms turn-and-river pause, so it would run while the player reads the river cards with the prompt appearing when done, or be dropped if John prefers no hint. The expert should measure that count on the board before the build.

## Options
### A. Standard rules (recommended)
- Equal **Ante and Blind**. Two hole cards to the player and the dealer, five community cards dealt face down.
- **Pre-flop:** raise **4x** the Ante (3x also offered, DR-045 decides whether to expose it) or check. **Flop** (three community cards): a checked player may raise **2x** or check. **Turn and river** (the last two together): a twice-checked player raises **1x** or **folds** (losing Ante and Blind).
- Showdown: best five of seven for both. **Dealer qualifies with a pair or better**; otherwise the Ante pushes. Player wins: Play pays 1:1, Ante pays 1:1 if the dealer qualified, Blind pays by the table for a straight or better and pushes below. Player loses: Ante, Blind and Play lost. Tie: all push.
- **Blind table:** royal flush 500:1, straight flush 50:1, four of a kind 10:1, full house 3:1, flush 3:2, straight 1:1, less than a straight push.
- **No Trips side bet** in version 1 (a separate request if wanted; it has its own paytable and about a 1.9% edge).
- Other players at the table (DR-044) play against the house only and never change these odds.

### B. Different Blind table (e.g. royal 500:1 with flush 3:2 and quads 10:1 but full house 4:1)
- Cons: variants exist, but the one above is the WSOP/common table and the one with a published edge to check against.

## Recommendation
Option A. The game's help screen (X) shows the simple strategy in plain words: pre-flop raise 4x with any pair but twos, any ace, K-5+ (K-2+ suited), Q-8+ (Q-6+ suited), J-10 (J-8+ suited); after the flop raise 2x with two pair or better, a pair using one of your cards, or four to a flush with a 10 or better in your hand; after the river raise 1x with any pair using your cards, else fold.

## What John would have to do or accept
House edge about 2.2% of the Ante with expert play, about 6.6% with the simple rules on the help screen. With a 10-chip Ante the average loss is about 0.7 chips per hand on the simple rules.

## Appendix
`python3 tools/uth_edge.py`. Reference: https://wizardofodds.com/games/ultimate-texas-hold-em/ (rules verified 2026-10-04). Exposure per hand: Ante + Blind + 4x Play = 6x Ante (DR-046).
