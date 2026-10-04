# DR-062: John's flop game ("Caribbean" as he wants it played): the rules

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-06
- **Blocks:** The flop game's engine. The baccarat requests (DR-051 to DR-060) stay filed; the PM sets the order.
- **Needs HW review:** no (the screen request DR-066 has the review)

## The decision
John described (directly, 2026-10-06) how he wants "Caribbean" played: a set bet, two cards to him, two to the dealer and two to each other player, the first three table cards turn, he bets low or high or folds, the last two turn, and "the 4s or better rules apply". That is **Casino Hold'em** (a published game) with a low/high call. This request fixes the frame; DR-063 the call sizes, DR-064 his multiplier rule.

## Why it matters
It is a new game, not a change to Caribbean Stud, so scope and the fate of the Stud build need a ruling, and the pays set the house edge.

## Options
### A. Casino Hold'em rules; it takes the Caribbean row; Caribbean Stud is kept as a fifth row (recommended)
- **Ante** with the joystick (DR-068). **Two cards** to the player face up, two to the dealer face down, two to each seat (DR-069); five table cards face down.
- **Flop:** the first three table cards turn. The player **folds** (losing the Ante) or **calls** low or high (DR-063).
- **Turn and river:** the last two table cards turn, then the dealer's cards. Best five of seven for each.
- **Dealer qualifies with a pair of fours or better** ("4s or better"). Not qualified: the Ante is paid (how much is part of DR-063) and the call pushes. Qualified and beaten: the Ante pays by the table below and the call 1:1. Dealer wins: Ante and call lost. Tie: push.
- **Ante table:** royal flush 100:1, straight flush 20:1, four of a kind 10:1, full house 3:1, flush 2:1, anything else 1:1 (the published Casino Hold'em table).
- **Published reference:** with a fixed 2x call and optimal play the house edge is **2.16% of the Ante** (Wizard of Odds). Our simulator `tools/casino_holdem_edge.py`, playing a simple written strategy (fold with nothing, call with a pair, a draw, an ace or a card above the board), measures the fixed-2x game at about **7.6%**, so the strategy on the help screen costs about 5 points over expert play, as the first Ultimate strategy did; the numbers for the low/high variants are in DR-063.
- **Menu:** the new game takes the "Caribbean" row with a new label (John to name it; "Casino" fits nine characters; the help screen says "Casino Hold'em"). Caribbean Stud moves down a row as "Stud" so nothing John said was good is thrown away. RAM allows it: games load one at a time (STATUS report of 2026-10-06).
- Cons: five game rows plus Off; one more scroll to reach Off.

### B. The same rules, but Caribbean Stud is removed (archived like slots)
- Pros: a shorter menu.
- Cons: a finished, tested game John said was good goes to the archive for nothing; it costs no RAM while another game runs.

### C. Change Caribbean Stud itself to these rules
- Cons: nothing of Stud's rules survives (five cards each, A-K qualifier, raise 2x); it is a new game in Stud's clothes.

## Recommendation
Option A. The published game is a faithful match to John's description, so John can check its rules anywhere; DR-063 is where his low/high idea lives.

## What John would have to do or accept
Name the new row (nine characters or fewer). Accept Caribbean Stud staying on the menu as "Stud", or rule B to drop it. The house edge depends on DR-063 and DR-064.

## Appendix
Reference: https://wizardofodds.com/games/casino-holdem/ (rules checked 2026-10-06). Simulator noise: about plus or minus 1 point of the Ante at 200,000 hands per row.
