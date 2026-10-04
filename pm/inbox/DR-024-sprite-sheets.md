# DR-024: Sprite sheets: one file per family of images instead of one file per image

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-05
- **Blocks:** nothing today (code-drawn cards and symbols work). Should be ruled **before John converts and uploads the card art**, so it is converted once.
- **Needs HW review:** yes. The numbers below are the expert's (HR-F03 re-check after step 1f): `open()` about 3 ms on LittleFS; `os.stat` 3.7 ms (already cached away); read of a 4,480-byte card about 1 ms; keyed blit about 1 ms; a card from its own file 5.6 ms; code-drawn card 3.9 ms. What is new to measure: a card from a sheet (expected about 2 ms) and the slot reels reading rows from a sheet instead of per-symbol files.

## The decision
Whether the converter packs each family of same-size images (the 53 cards, the chips, the banners, the icons, the 8 slot symbols) into one `.565` file per family, with the loader opening that file once per scene and seeking to each sprite.

## Why it matters
The expert measured that opening a file costs about 3 ms on this filesystem, every time, and it grows with the number of files in the folder. A blackjack result scene draws up to eight cards and a banner: with one file per card that is about 45 ms of blits, slower than the code-drawn cards it replaces (31 ms). John's card art would make the game slower. With one open per scene a card costs about 2 ms, so the art makes the game faster, and 53 uploads become one.

## What changes for John: nothing
He still draws **53 separate 40 x 56 BMPs** named as in `assets/ASSETS.md` (`c_AS.bmp` ... `c_back.bmp`), same for chips, banners, icons and symbols. The packing is a converter step. The pilot flow (make `c_AS`, `c_back`, `chip_5`, `table` first) still works: a sheet with missing members is written with magenta (transparent) placeholders for the missing cards and the converter lists them, so a partial card set is playable and the code-drawn card shows for the rest.

## Options
### A. Sheets for every family (recommended)
- **File format:** the same `.565` header (width, height) with the sprites stacked vertically: `cards.565` is 40 wide and 53 x 56 = 2,968 tall, 237,444 bytes. Sprite `n` starts at byte 4 + n x 4,480. The loader validates the file length exactly as today (DR-002), so nothing in the format rules changes; a sheet is simply a tall image.
- **Families and order** (one list, `lib/sheets.py`, used by both the converter and the loader):
  - `cards.565`: the 52 cards in the engine's card order (`cards.py`: index = suit x 13 + rank, spades, hearts, diamonds, clubs), then `c_back` as sprite 52.
  - `chips.565`: `chip_5, chip_25, chip_100, chip_500` (and `chip_1` if John draws it).
  - `banners.565`: `banner_win, banner_lose, banner_push, banner_bust, banner_blackjack, banner_jackpot` (all 160 x 32 except jackpot at 200 x 40, so **jackpot stays its own file**; the five blackjack banners share a sheet).
  - `icons.565`: `icon_blackjack, icon_slots, icon_stud, icon_holdem` (48 x 48).
  - `symbols.565`: the 8 slot symbols in `slots_rules.SYMBOLS` order (56 x 56). The reels then seek within one file that stays open for the whole spin: **no file open at all during a spin**, which removes the 3 ms open on every symbol change in the current build.
  - Full-screen images (`table`, `cabinet`, `menu_background`) and the `logo` stay single files.
- **Loader API:** `Assets.sheet(name)` returns a `Sheet` (open file, sprite size, count) with `blit(fb, index, x, y)`, `rows(index, first, n, dst)` for the reels, and `close()`. A scene opens its sheets on entry and closes them on exit. The old `blit('c_AS')` keeps working as a fallback when the sheet is missing, so the pilot and the code-drawn paths are unchanged.
- **RAM:** one open file object per sheet in use (about 100 bytes each); the 16 KB scratch is unchanged. **Flash:** the same pixel bytes, 52 fewer headers; 67 files in `/assets` become about 12.
- **Cost:** converter packing step and tests, `lib/sheets.py`, `Sheet` in `art.py`, blackjack and slots switched to sheets with fallback: about half a day. `UPLOAD.md` step 2 changes from "upload each `.565`" to "upload the sheet files".
- **Cons:** a change to one card means re-running the converter and re-uploading the 237 KB sheet, not one 4 KB file.

### B. A sheet for the cards only
- Pros: fixes the measured problem (cards) with the least change.
- Cons: the slot reels keep one file open per symbol change (3 ms, once every 7 frames per reel); chips and banners keep 3 ms per blit.

### C. Keep one file per image
- Cons: card art makes blackjack slower than today. Rejected by the measurement.

## Recommendation
Option A. I would take B if the expert measures no gain for the reels or the PM wants the smallest change.

## What John would have to do or accept
Nothing changes in how he draws. Uploads get easier: one `cards.565` instead of 53 files. He accepts that fixing one card later means re-converting and re-uploading the sheet.

## Appendix
Expert's measurements: `hw/reviews/HR-F03.md` (re-measured after step 1f), `hwtest/blit_bench.py`. Expected card cost from a sheet: seek + 4,480-byte read about 1 ms (5.6 MB/s) + keyed blit about 1 ms. Current per-file card: 5.6 ms. Code-drawn: 3.9 ms.
