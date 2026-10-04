# DR-058: Baccarat: the help screen

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-06
- **Blocks:** Nothing
- **Needs HW review:** no (same shape as `stud_pay` and `holdem_pay`, 200 ms to show, measured)

## The decision
What X shows: the pays and the third-card rules in plain words.

## Options
### A. One screen: pays, card values, the Player's rule, the Banker's rule, the edges (recommended)
Proposed text, 29 characters per line at most (the text test enforces it), gold for the headings:

```
Baccarat (punto banco)
Player 1:1   Tie 8:1
Banker 1:1 less 5%: 19 for 20,
rounded down. Tie: Player
and Banker bets push.

CARDS: A=1, 2-9 face value,
10 J Q K = 0. Only the last
digit counts. 8 or 9 on two
cards is a natural: no draw.
PLAYER draws on 0-5, stands
on 6-7.
BANKER if Player stood: same.
If Player drew card v: draws
on 0-2; 3 unless v=8; 4 on
2-7; 5 on 4-7; 6 on 6-7.
Edge: Banker 1.1% Player 1.2%
Tie 14.4%         any key: back
```
- The rules are the standard tableau (DR-051); the edges are the measured ones. The commission wording follows DR-059.
- Pros: a player who has never seen baccarat learns in one screen that there is nothing to decide after the bet.

### B. Pays only
- Cons: the third-card rules are the one thing players ask about, and the game draws cards "for no reason" without them.

### C. Two screens (pays, then rules)
- Cons: it fits on one.

## Recommendation
Option A.

## What John would have to do or accept
Nothing. He can ask for different wording in the ruling.
