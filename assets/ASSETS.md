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
| `ui/logo.bmp` | 1 | **200 x 40** | 16,004 | "Pocket Chance" title, magenta background |
| `ui/icon_blackjack.bmp`, `icon_slots.bmp` | 2 | **48 x 48** | 4,612 each | Menu icons |
| `ui/banner_win.bmp`, `banner_lose`, `banner_push`, `banner_bust`, `banner_blackjack` | 5 | **160 x 32** | 10,244 each | Short result banners drawn over the table, magenta background |

Phase 1 total: 66 files, roughly 0.43 MB (each file carries a 4-byte size header). The card set is 237 KB of that.

**Hand fit:** five 40 px cards side by side take 200 px. A sixth card overlaps the others. This is why the card width is 40.

## Phase 2: slots

| File | Count | Size (px) | Bytes on board | Notes |
|---|---|---|---|---|
| `slots/sym_<name>.bmp` | 8 | **56 x 56** | 6,276 each | Names: `cherry`, `lemon`, `orange`, `bell`, `bar`, `seven`, `diamond`, `star`. Each fills its square on a solid or simple background, no transparency needed |
| `slots/cabinet.bmp` (optional) | 1 | **240 x 240** | 115,204 | Machine frame. Leave three **56 x 56** windows, centred vertically, with 18 px gaps. The reels are drawn into those windows. The dev may adjust positions in a ruling |
| `slots/banner_jackpot.bmp` | 1 | **200 x 40** | 16,004 | Magenta background |
| `slots/sym_blur.bmp` (optional) | 1 | **56 x 56** | 6,276 | A motion-blurred strip to show while the reels spin |

## Notes for the senior dev

- **File format (DR-002):** `.565` = 4-byte header (width, height, each 16-bit little-endian) followed by RGB565 pixels, row by row, top-left first. The loader checks the file length against the header and refuses mismatches.
- **Byte order (DR-003, confirmed on the panel 2026-10-04):** pixels are big-endian RGB565 (`F8 00` is red) and are copied into the framebuffer unchanged. Colours in code are the byte-swapped value from `pixfmt.rgb(r, g, b)`.
- **Transparency:** #FF00FF converts to bytes `F8 1F`, which framebuf reads as the key `0x1FF8` (`pixfmt.KEY`). The converter nudges any non-magenta pixel that would land on that value by one shade of blue, so real pixels never go invisible.
- **Orientation (DR-003/006):** `0x36 = 0x70` gives upright landscape; framebuffer (0,0) is the player's top-left. No rotation in the converter.
- **Loading (DR-005):** sprites go through one 16 KB scratch buffer and `blit` with the key; full-screen images are read with one `readinto` into the framebuffer on scene entry only, and partial rows are re-read for band redraws. Nothing full-screen stays in RAM.
