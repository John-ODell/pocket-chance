# DR-061: Rename the Hold'em menu row to "Ultimate"

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-06
- **Blocks:** Nothing (a one-line change once ruled)
- **Needs HW review:** no

## The decision
John asked (directly, 2026-10-06): "First rename holdem to ultimate." This changes the menu word ruled in DR-049.

## Options
### A. Menu row "Ultimate" (recommended)
- Eight characters, fits the nine the menu allows. The help screen title stays "Ultimate Texas Hold'em". `pocket.py` menu tuple, `README.md`, `assets/ASSETS.md` icon name unchanged (`icon_holdem`; the file name is not shown).
- Cons: none; "Caribbean" will likely be renamed too (DR-062), so the menu would read Blackjack, Ultimate, <new name>, Baccarat, Off.

### B. Keep "Hold'em"
- Cons: John has asked for the change.

## Recommendation
Option A. One line plus the README; upload `pocket.py` (a new `UPLOAD.md` step).

## What John would have to do or accept
Re-upload `pocket.py` when the step is listed.
