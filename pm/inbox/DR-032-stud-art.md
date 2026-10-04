# DR-032: Caribbean Stud: which art it uses

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-05
- **Blocks:** John's art list
- **Needs HW review:** no

## The decision
What Caribbean Stud draws with, and whether John needs to draw anything new.

## Options
### A. Reuse everything; one optional new banner (recommended)
- Cards: the blackjack `cards.565` sheet (52 faces and the back). Chips: `chips.565`. Table: `table.565` (same felt). Result banners: `banner_win`, `banner_lose`, `banner_push` from `banners.565`; the fold result is drawn as text.
- One optional new picture: **`banner_noqualify`**, 160 x 32, magenta background, "DEALER DOES NOT QUALIFY" or similar, added to the `banners.565` family as member 6 (after `banner_blackjack`); until John draws it the game writes the words. Menu icon `icon_stud` (48 x 48) is already in the icons family.
- Pros: nothing blocks the game on art; John draws one banner and one icon if he wants to.
- Cons: none.

### B. A dedicated Stud table background
- Cons: another 115 KB image to draw and upload for the same felt.

## Recommendation
Option A. `assets/ASSETS.md` gains the one banner row and the sheet member.

## What John would have to do or accept
Optionally draw `banner_noqualify.bmp` (160 x 32) and `icon_stud.bmp` (48 x 48). Nothing else.
