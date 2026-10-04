# DR-021: Slots: how wins are shown, paytable screen, no auto-spin

- **Status:** pending, **revision 2** (2026-10-05): the order of save and blink is fixed per the expert's HR-021; the write-rate question is answered (harmless).
- **Filed by:** senior dev
- **Date:** 2026-10-04
- **Blocks:** Slots screen
- **Needs HW review:** yes. Done: HR-021 (fits). Measured: one blink toggle of the three gold frames 58 ms (85 max); one save 54 to 77 ms mean, 102 to 151 ms max; about 1,000 writes per hour of continuous play, which the expert puts at thousands of times below any wear concern.

## The decision
What happens after the reels stop, how the jackpot is shown, whether a paytable is visible in the game, and whether the machine can spin by itself.

## Options
### A. Highlight the winning line, show the amount in the bottom band, jackpot banner, paytable on X, no auto-spin (recommended)
- **Order after the last reel stops (HR-021 limits):** the three windows are drawn into the framebuffer, the win is evaluated, the `$` line and the bottom band ("WIN +40" in gold with the line name, e.g. "two cherries"; "no win" in grey) are drawn and pushed, **then the bankroll is saved** (54 to 151 ms, while the player reads the result), **then** on a win the gold frames around the three windows blink 3 times (about 58 ms per toggle, measured; pushed as one 240-row band if it ever needs to be faster). The save never runs between reel stops or during the blink, so neither stutters.
- Three stars: `banner_jackpot` art (200 x 40) in the bottom band for 2 seconds with a longer blink, then the win line.
- **X** shows a paytable screen (plain text table of the lines and pays from DR-018 at the current bet; any key returns). This is how the player learns the odds.
- No auto-spin in version 1: every spin is a press of A. One save per spin (DR-007 rule). HR-021: about 1,000 writes an hour at the fastest a human plays, against a wear horizon the expert puts at hundreds of thousands of hours; "save only when the balance changed" is not needed, and the balance changes on every spin anyway.
- Cons: the save adds 54 to 151 ms to the pause after each spin; the player is reading the result then, so it is not felt.

### B. Also an auto-spin (hold A)
- Cons: encourages mindless draining of the bankroll. The write rate would still be harmless (HR-021). Later, if asked.

### C. No highlight, just the text
- Cons: wins are easy to miss.

## Recommendation
Option A.

## What John would have to do or accept
The `banner_jackpot` art (200 x 40, magenta background) from the Phase 2 list; without it a code-drawn "JACKPOT!" is shown.
