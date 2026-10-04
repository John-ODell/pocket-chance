# DR-049: Ultimate Texas Hold'em: menu label and art

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-05
- **Blocks:** Nothing
- **Needs HW review:** no

## The decision
The menu word and what the game draws with.

## Options
### A. Label "Hold'em"; reuse all art; no new pictures (recommended)
- Menu row "Hold'em" (already on the board from DR-022; "Ultimate Hold'em" does not fit at size 2). The screen title reads "Ultimate Texas Hold'em" in the help screen.
- Cards from `cards.565`, chips from `chips.565`, table from `table.565`; results as text in the 36 px bottom band, or `banner_win` / `banner_lose` / `banner_push` (160 x 32) at y 204; `banner_noqualify` is reused for "dealer does not qualify, Ante pushes". Seat strips are code-drawn text.
- Optional: `icon_holdem` (48 x 48) in the icons sheet.
- Pros: nothing blocks the game on art.

### B. New Blind-paytable banner art
- Cons: the Blind pays appear on the help screen as text; a banner adds nothing.

## Recommendation
Option A.

## What John would have to do or accept
Optionally draw `icon_holdem.bmp`. Nothing else.
