# DR-057: Baccarat: menu label, icon and art

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-06
- **Blocks:** Nothing
- **Needs HW review:** no

## The decision
The menu word, the icon slot and what the game draws with.

## Options
### A. Label "Baccarat"; a fourth icon slot `icon_baccarat`; all other art reused (recommended)
- "Baccarat" is eight characters, within the nine the menu allows at size 2. The row goes after "Hold'em" and before "Off", so the menu becomes five rows with three visible, scrolling as today (DR-022). The help screen's title reads "Baccarat (punto banco)".
- `icons.565` grows from three to four 48 x 48 slots (`blackjack, stud, holdem, baccarat`); `lib/sheets.py`, `assets/ASSETS.md` and the sheet tests change with it. No icons sheet is on the board yet, so nothing has to be re-converted; until John draws the icon, the row shows the plain plate as the others do.
- Cards from `cards.565`, chips from `chips.565`, table from `table.565`; results and the bet boxes are code-drawn text.
- Pros: nothing blocks the game on art.

### B. Label "Punto" or "Banco"
- Cons: the casino name for the game is baccarat and it fits.

### C. New art for the bet boxes (a painted layout strip, 240 x 28)
- Cons: `fill_rect` boxes and text do the job; a strip adds a file and a readability zone for no gain. Can be a later request if the code-drawn boxes look poor.

## Recommendation
Option A.

## What John would have to do or accept
Optionally draw `icon_baccarat.bmp` at 48 x 48. The menu gains a row; Off is one more press away.
