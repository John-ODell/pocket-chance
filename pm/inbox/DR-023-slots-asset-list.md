# DR-023: Slots: confirm the Phase 2 art list, window positions and readability zones

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-04
- **Blocks:** John's Phase 2 art
- **Needs HW review:** no

## The decision
Fix the Phase 2 asset list so John can draw it: names, sizes, where the windows sit in the cabinet, and which areas stay calm.

## What changes from the current `assets/ASSETS.md`
1. **Symbols:** 8 files `sym_cherry`, `sym_lemon`, `sym_orange`, `sym_bell`, `sym_bar`, `sym_seven`, `sym_diamond`, `sym_star`, **56 x 56**, no transparency, as listed. Unchanged.
2. **Cabinet** `cabinet`, **240 x 240**, optional (the game draws a plain frame without it). The three windows are fixed at **x 18 to 73, 92 to 147, 166 to 221; y 92 to 147** (56 x 56 each, 18 px gaps and margins, centred vertically). The cabinet art under the windows is never seen; everything else is.
3. **Jackpot banner** `banner_jackpot`, **200 x 40**, magenta background, drawn at x 20 to 219, y 176 to 215. Unchanged.
4. **Dropped:** `sym_blur`. The reels scroll the real symbols (DR-020), so a blur frame is not needed.
5. **Readability zones** (same rule as the table: dark and calm under text, average brightness under 100 of 255):
   - top band y 0 to 23: `$chips` at x 6 to 118 and the bet at x 150 to 234, as in blackjack;
   - a "win line" y 156 to 166, x 20 to 220 (the line name, e.g. "two cherries");
   - bottom band y 168 to 239: banner x 20 to 220, y 176 to 215; prompt lines y 218 to 226 and y 228 to 236, x 20 to 220.
   The reel band y 24 to 155 outside the windows is free for decoration (lights, chrome), as long as it is not pure magenta.
   The converter will warn on these zones for `cabinet` the way it does for `table`.
6. Flash: 8 x 6,276 + 115,204 + 16,004 = about 181 KB. Trivial.

## Options
### A. Adopt the list above (recommended)
### B. Keep `sym_blur` and the "dev may adjust positions" wording
- Cons: an unused file for John to draw, and positions that are not fixed yet.

## Recommendation
Option A. John can start with `sym_cherry`, `sym_star` and `sym_bar` as pilot files; the rest can follow.

## What John would have to do or accept
Draw 8 symbols, the cabinet (optional) and the jackpot banner at the sizes above, upright, same BMP rules as Phase 1. The converter already knows the names and sizes.
