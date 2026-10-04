# Art asset spec

**Status: approved** (rulings DR-002, DR-003, DR-006 on 2026-10-04). Sizes below are final. **Make the four pilot files first** (`c_AS`, `c_back`, `chip_5`, `table`) and run them through the converter and the board before drawing the rest.

**Which way up:** draw everything upright as you see the screen while playing, with the USB-C plug and joystick on the left and the four buttons on the right. The converter does not rotate anything.

The screen is **240 x 240 pixels**. Everything is tiny, so draw big, simple shapes with strong contrast.

## File format (for everything)

| Item | Requirement |
|---|---|
| Type | **BMP, 24-bit**, uncompressed, no alpha channel, no colour profile. PNG also works, and the converter accepts both |
| Size | **Exact pixel size** from the tables. Wrong-sized files are rejected, not stretched |
| Transparency | Fill the transparent area with pure magenta, **RGB 255, 0, 255 (#FF00FF)**. Nothing else |
| Edges | **No anti-aliasing against magenta.** Smooth edges blend into pink and leave a visible fringe on the board. Use hard pixel edges, or bake the soft edge onto the background it will sit on |
| Colours | The panel shows 5-6-5 bit colour, so smooth gradients show visible bands. Use flat colours with 3 to 5 shades per hue, or dither. Keep the dark and light shades well apart |
| Names | Lowercase, no spaces, exactly as in the tables |
| Where | `assets/src/<folder>/` as listed. The converter writes the board files flat into `assets/out/<name>.565`, and they are uploaded to `/assets/` on the board |
| Converting | From the repo folder: `python3 tools/convert_assets.py`. It checks every size and name, and refuses wrong ones with a message. `--resize` scales a wrong-sized file with nearest-neighbour instead |

Free editors that export exact-size 24-bit BMP: Aseprite (paid, best for pixel art), Pixelorama, Piskel (web), GIMP. macOS Preview can open BMPs but is poor for editing them.

If you don't want to draw these, say so. The dev can generate simple versions in code, or you can send any image and the converter will resize it with nearest-neighbour scaling.

## Phase 1: blackjack

| File | Count | Size (px) | Bytes on board | Notes |
|---|---|---|---|---|
| `cards/c_<rank><suit>.bmp` | 52 | **40 x 56** | 4,484 each | Rank `A 2 3 4 5 6 7 8 9 T J Q K`, suit `S H D C`. Examples: `c_AS.bmp`, `c_TH.bmp`, `c_7C.bmp`. Cream or white face (not pure #FFFFFF, which glares on this panel), black spades and clubs, red hearts and diamonds. Rank and suit in the top-left corner large enough to read at a glance. Rounded corners: the 1-2 corner pixels are magenta |
| `cards/c_back.bmp` | 1 | **40 x 56** | 4,484 | Card back. Bold pattern in two or three colours |
| `chips/chip_5.bmp`, `chip_25`, `chip_100`, `chip_500` (`chip_1` optional, not used by blackjack, DR-014) | 4 | **24 x 24** | 1,156 each | Round, magenta outside the circle. Suggested colours: 5 red, 25 green, 100 black, 500 purple, (1 white). The value does not need to be readable. The dev prints the amount next to the chip |
| `ui/table.bmp` (optional: the game draws plain felt without it) | 1 | **240 x 240** | 115,204 | Felt table background. Dark green, a quiet border or edge line. **No text and no card shapes baked in.** Keep the top 24 px and bottom 40 px calm, since the dev draws the bankroll and bet there |
| `ui/menu_background.bmp` (optional) | 1 | **240 x 240** | 115,204 | Behind the main menu. Blurred or dark photos work best. Menu text sits on small dark plates so it stays readable, but keep the three row boxes (x 16–224, y 70–214) and the title area (y 8–60) from being very bright; the converter warns if they are. Supplied by John 2026-10-04 (D-007) |
| `ui/logo.bmp` | 1 | **200 x 40** | 16,004 | "Pocket Chance" title, magenta background |
| `ui/icon_blackjack.bmp`, `icon_stud.bmp`, `icon_holdem.bmp` | 3 | **48 x 48** | 4,612 each | Menu icons (packed into `icons.565`). `icon_holdem` is the Ultimate row, `icon_stud` the Caribbean row (the flop game inherited the slot when Caribbean Stud was archived) |
| `ui/banner_win.bmp`, `banner_lose`, `banner_push`, `banner_bust`, `banner_blackjack`, `banner_noqualify` | 6 | **160 x 32** | 10,244 each | Short result banners drawn over the table, magenta background. `banner_noqualify` ("dealer does not qualify") is for Caribbean Stud (DR-032), optional |

Phase 1 total: 67 files, roughly 0.54 MB (each file carries a 4-byte size header). The card set is 237 KB of that.

**Hand fit:** five 40 px cards side by side take 200 px. A sixth card overlaps the others. This is why the card width is 40.

## How your files reach the board: sheets (DR-024)

You draw **one BMP per picture**, exactly as listed above. The converter then packs each family of same-size pictures into **one file** for the board, because opening a file on the board costs about 3 ms and a hand of blackjack draws up to nine pictures:

| Sheet file on the board | Packed from | Sprite size | Members (in this order) | Bytes |
|---|---|---|---|---|
| `/assets/cards.565` | `cards/c_*.bmp` | 40 x 56 | the 52 cards, spades then hearts, diamonds, clubs, ace to king within each; then `c_back` | 237,444 |
| `/assets/chips.565` | `chips/chip_*.bmp` | 24 x 24 | `chip_1, chip_5, chip_25, chip_100, chip_500` | 5,764 |
| `/assets/banners.565` | `ui/banner_*.bmp` | 160 x 32 | `win, lose, push, bust, blackjack, noqualify` | 61,444 |
| `/assets/icons.565` | `ui/icon_*.bmp` | 48 x 48 | `blackjack, stud, holdem` | 13,828 |

`table`, `menu_background` and `logo` stay single files (`<name>.565`).

A picture you have not drawn yet becomes a transparent (magenta) placeholder inside the sheet, and the game draws its plain code version instead, so you can convert and upload after drawing just a few. The converter prints which members are missing. **When you change one picture, run the converter again and upload that family's sheet again** (one file).

## Readability: where text and cards sit on the blackjack table

The game draws over `table.565` in four horizontal bands that never overlap. Text is gold, white or grey, so under every text box the art must be **dark (average brightness under 100 of 255) and calm** (no bright pattern, no thin light lines). Cards and the chip cover their boxes completely, so the art under them does not matter. The converter prints a warning for any text box that is too light or too busy; it still converts the file. Everything below is in pixels, x from the left edge, y from the top, as you see the screen while playing.

| Band | Rows (y) | Text and cards | Keep dark and calm |
|---|---|---|---|
| Top | 0–23 | `$chips` in gold size-2 text at x 6–118, y 4–20. Chip icon at x 150–174. Bet digits in white, right-aligned ending at x 234, y 4–20 | the whole band |
| Dealer | 24–95 | Cards y 28–83, centred across x 12–228. `Dealer 17` in white at x 6–78, y 86–94 | x 0–100, y 84–96 |
| Player | 96–167 | Cards y 100–155, centred across x 12–228 (two hands at x 12–112 and 128–228 after a split). Totals at y 158–166: one hand at x 6–200, split hands at x 12–112 and 128–228, with a gold underline at y 167 | the whole strip y 156–168 |
| Bottom | 168–239 | Result banner (your `banner_*` art, 160 x 32) at x 40–200, y 168–200; without the art, size-2 text up to x 32–208, y 176–192. Two lines of small text at y 204–212 and 218–226, up to x 20–220 | x 16–224, y 168–240 |

**Main menu** (`menu_background`): the title plate is at x 16–224, y 11–33; the balance plate y 37–59; the three row boxes at x 16–224, y 70–118, 118–166, 166–214 (the selected row is a solid dark blue box, the others show the photo with a small dark plate under the word); the footer plate at y 223–237. The photo shows through the 16 px side margins, between the plates, and inside the unselected rows.

Good: a plain dark green felt with a slightly lighter border in the outer 12 px, a subtle logo or pattern in the card rows only (y 28–83 and 100–155, which the cards mostly cover), any decoration in the corners above y 24 is fine if it stays dark. Bad: light wood, bright gold trim or text under the four boxes above.

## Phase 2: slots (shelved, D-009, 2026-10-04)

Slots was dropped: John does not need to draw any slot art. The old spec is in git history and
`archive/slots/`, and Caribbean Stud in `archive/stud/` (John's ruling, 2026-10-06). Ultimate and the
new Caribbean flop game reuse the cards, chips and table; `banner_noqualify` stays in the sheet (member order never changes) but no game shows it now.

## How your files reach the board: sheets (DR-024)

You draw **one BMP per picture**, exactly as listed above. The converter then packs each family of same-size pictures into **one file** for the board, because opening a file on the board costs about 3 ms and a hand of blackjack draws up to nine pictures:

| Sheet file on the board | Packed from | Sprite size | Members (in this order) | Bytes |
|---|---|---|---|---|
| `/assets/cards.565` | `cards/c_*.bmp` | 40 x 56 | the 52 cards, spades then hearts, diamonds, clubs, ace to king within each; then `c_back` | 237,444 |
| `/assets/chips.565` | `chips/chip_*.bmp` | 24 x 24 | `chip_1, chip_5, chip_25, chip_100, chip_500` | 5,764 |
| `/assets/banners.565` | `ui/banner_*.bmp` | 160 x 32 | `win, lose, push, bust, blackjack, noqualify` | 61,444 |
| `/assets/icons.565` | `ui/icon_*.bmp` | 48 x 48 | `blackjack, stud, holdem` | 13,828 |

`table`, `menu_background` and `logo` stay single files (`<name>.565`).

A picture you have not drawn yet becomes a transparent (magenta) placeholder inside the sheet, and the game draws its plain code version instead, so you can convert and upload after drawing just a few. The converter prints which members are missing. **When you change one picture, run the converter again and upload that family's sheet again** (one file).

## Readability: where text and cards sit on the blackjack table

The game draws over `table.565` in four horizontal bands that never overlap. Text is gold, white or grey, so under every text box the art must be **dark (average brightness under 100 of 255) and calm** (no bright pattern, no thin light lines). Cards and the chip cover their boxes completely, so the art under them does not matter. The converter prints a warning for any text box that is too light or too busy; it still converts the file. Everything below is in pixels, x from the left edge, y from the top, as you see the screen while playing.

| Band | Rows (y) | Text and cards | Keep dark and calm |
|---|---|---|---|
| Top | 0–23 | `$chips` in gold size-2 text at x 6–118, y 4–20. Chip icon at x 150–174. Bet digits in white, right-aligned ending at x 234, y 4–20 | the whole band |
| Dealer | 24–95 | Cards y 28–83, centred across x 12–228. `Dealer 17` in white at x 6–78, y 86–94 | x 0–100, y 84–96 |
| Player | 96–167 | Cards y 100–155, centred across x 12–228 (two hands at x 12–112 and 128–228 after a split). Totals at y 158–166: one hand at x 6–200, split hands at x 12–112 and 128–228, with a gold underline at y 167 | the whole strip y 156–168 |
| Bottom | 168–239 | Result banner (your `banner_*` art, 160 x 32) at x 40–200, y 168–200; without the art, size-2 text up to x 32–208, y 176–192. Two lines of small text at y 204–212 and 218–226, up to x 20–220 | x 16–224, y 168–240 |

**Main menu** (`menu_background`): the title plate is at x 16–224, y 11–33; the balance plate y 37–59; the three row boxes at x 16–224, y 70–118, 118–166, 166–214 (the selected row is a solid dark blue box, the others show the photo with a small dark plate under the word); the footer plate at y 223–237. The photo shows through the 16 px side margins, between the plates, and inside the unselected rows.

Good: a plain dark green felt with a slightly lighter border in the outer 12 px, a subtle logo or pattern in the card rows only (y 28–83 and 100–155, which the cards mostly cover), any decoration in the corners above y 24 is fine if it stays dark. Bad: light wood, bright gold trim or text under the four boxes above.

## Phase 2: slots (approved, DR-023, 2026-10-04)

**At a glance, for John.** Ten files. Start with the three pilot files **`sym_cherry`, `sym_star`, `sym_bar`**, run them through the converter, and the game shows them before you draw the rest.

| File | Count | Size (px) | Bytes on board | Notes |
|---|---|---|---|---|
| `slots/sym_cherry.bmp`, `sym_lemon`, `sym_orange`, `sym_bell`, `sym_bar`, `sym_seven`, `sym_diamond`, `sym_star` | 8 | **56 x 56** | 6,276 each | One symbol each, filling its square on a solid or simple dark background. **No transparency** (no magenta): the whole square is shown. Bold shapes, 3 to 5 flat colours. `star` is the jackpot, `cherry` the small win, so make those two the most distinct |
| `slots/cabinet.bmp` (optional) | 1 | **240 x 240** | 115,204 | The machine frame. The game draws the three reels into fixed windows at **x 18–73, 92–147 and 166–221, y 92–147** (56 x 56 each). Whatever you paint inside the windows is never seen. Keep the text zones below dark and calm. Without this file the game draws a plain frame |
| `slots/banner_jackpot.bmp` | 1 | **200 x 40** | 16,004 | "JACKPOT" banner, magenta background, shown at x 20–219, y 176–215 when three stars land |

`sym_blur` is dropped: the reels scroll the real symbols, so no blur frame is needed.

**Readability zones on the cabinet** (same rule as the table: average brightness under 100 of 255 and no bright pattern; the converter warns if not):

| Zone | Pixels | What is drawn there |
|---|---|---|
| Top line | x 0–240, y 0–23 | `$chips` in gold at x 6–118; chip and bet at x 150–234 |
| Win line | x 20–220, y 156–166 | the winning line's name, e.g. "two cherries" |
| Bottom band | x 16–224, y 168–239 | jackpot banner (y 176–215), win amount and the prompt lines (y 218–226, 228–236) |

The reel band (y 24–155) outside the three windows is yours for lights, chrome and decoration.

## Notes for the senior dev

- **File format (DR-002):** `.565` = 4-byte header (width, height, each 16-bit little-endian) followed by RGB565 pixels, row by row, top-left first. The loader checks the file length against the header and refuses mismatches.
- **Byte order (DR-003, confirmed on the panel 2026-10-04):** pixels are big-endian RGB565 (`F8 00` is red) and are copied into the framebuffer unchanged. Colours in code are the byte-swapped value from `pixfmt.rgb(r, g, b)`.
- **Transparency:** #FF00FF converts to bytes `F8 1F`, which framebuf reads as the key `0x1FF8` (`pixfmt.KEY`). The converter nudges any non-magenta pixel that would land on that value by one shade of blue, so real pixels never go invisible.
- **Orientation (DR-003/006):** `0x36 = 0x70` gives upright landscape; framebuffer (0,0) is the player's top-left. No rotation in the converter.
- **Loading (DR-005):** sprites go through one 16 KB scratch buffer and `blit` with the key; full-screen images are read with one `readinto` into the framebuffer on scene entry only, and partial rows are re-read for band redraws. Nothing full-screen stays in RAM.
