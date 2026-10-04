# DR-021: Slots: how wins are shown, paytable screen, no auto-spin

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-04
- **Blocks:** Slots screen
- **Needs HW review:** yes

## The decision
What happens after the reels stop, how the jackpot is shown, whether a paytable is visible in the game, and whether the machine can spin by itself.

## Options
### A. Highlight the winning line, show the amount in the bottom band, jackpot banner, paytable on X, no auto-spin (recommended)
- On a win: the three windows get a gold frame that blinks 3 times (three 56 x 56 window pushes per blink, about 5 ms each) and the bottom band shows "WIN +40" in gold with the line name ("two cherries"). The `$` line updates. On no win: "no win" in grey.
- Three stars: `banner_jackpot` art (200 x 40) in the bottom band for 2 seconds with a longer blink, then the win line.
- **X** shows a paytable screen (plain text table of the lines and pays from DR-018 at the current bet; any key returns). This is how the player learns the odds.
- No auto-spin in version 1: every spin is a press of A. The save happens once per spin, after the result is drawn (DR-007 rule, the same as blackjack).
- Cons: the save once per spin is more writes than blackjack, roughly one every 3 to 4 seconds while playing. The expert's budget calls one write per round harmless (100,000-cycle flash, LittleFS spreads writes); at a spin every 4 seconds that is 900 writes an hour. If the expert prefers, I can save only when the balance changed, which is most spins anyway.

### B. Also an auto-spin (hold A)
- Cons: encourages mindless draining of the bankroll and makes the write rate higher. Later, if asked.

### C. No highlight, just the text
- Cons: wins are easy to miss.

## Recommendation
Option A.

## What John would have to do or accept
The `banner_jackpot` art (200 x 40, magenta background) from the Phase 2 list; without it a code-drawn "JACKPOT!" is shown.
