# DR-042: Ultimate Texas Hold'em: rules, Blind paytable and house edge

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-05
- **Blocks:** The Hold'em engine
- **Needs HW review:** no

## The decision
The rules of Ultimate Texas Hold'em as this device plays it, and the Blind paytable.

## Why it matters
This sets the house edge. Figures: the published reference (Wizard of Odds) is **2.185% of the Ante with optimal play** and **2.43% with the Wizard's "simple strategy"**. Our simulator (`tools/uth_edge.py`) currently measures the published simple strategy at about 6.9% of the Ante (1.6% of all chips staked, since the Play bet is large), which does not match the published 2.43%; see the next section. Raising 3x instead of 4x before the flop costs about 9 more points: always 4x.

## The help screen and the house edge: a product decision for John
The published figures are 2.185% of the Ante with optimal play and 2.43% with the Wizard's "simple strategy". Our simulator implements that simple strategy from the published text and measures **about 6.9% of the Ante** (400,000 hands, 8 seeds), both with and without the river "fewer than 21 dealer outs" rule; the two differ only in fold rate (10.8% vs 14.7%), not in result. So either my reading of the outs rule is wrong or another part of my strategy code is, because the published figure is well established. **I have not resolved this yet** and will not build the help screen until the simulator reproduces a figure I can defend. Two honest statements stand: 4x is always the better pre-flop raise (3x costs about 9 more points), and the player's edge depends heavily on the river decision.

The decision for John: a help screen that teaches a strategy losing 6 to 7% of the Ante when a published one loses 2.4% makes the player lose faster than necessary. My recommendation is to **teach the full published simple strategy**, including the river rule in plain words, and, if the expert finds it affordable, show the dealer-outs count on the river prompt (45 unseen cards, each checked against the board: about 45 seven-card evaluations, estimated 0.5 to 1 s on this board, run during the turn-and-river pause). If that is too slow, the help text teaches the rule and the player counts for themselves. I will report the corrected measurement in a revision before the Hold'em build starts.

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
