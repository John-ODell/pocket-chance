# DR-072: The main menu's look: three code-drawn styles

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-06
- **Blocks:** Nothing (the menu works as it is)
- **Needs HW review:** yes (menu entry redraw time and the row-band pushes; no new buffers). **Reviewed as built (HR-072, tip d861e16): fits.** The menu code is 2.6 KB of RAM, so free RAM at boot is **65.7 KB** (was 68.0); entry 130 ms mean, a joystick move 44 ms, a scroll 40 ms.

## The decision
John wants the menu to look good: today, without his photo file on the board, it is a dark screen with text, three plain row boxes and a gold frame around the chosen one. Which of the three styles below (all drawn in code, no art needed, no photo, nothing we do not own) does the menu get?

## Why it matters
The menu is the first screen John sees every time. It must stay cheap: entry today is one full redraw (about 60 ms with the photo), a joystick move two 48-row band pushes (about 55 ms), and the icon sheet is the only file open. A style that needs a buffer or a file per row would eat the RAM headroom every game relies on.

## What stays the same in every option
Three 48 px rows with the list scrolling (DR-022), the 9-character labels, the icon slot at the left of each row (John's `icon_*` art drops in when drawn), the title and chips at the top, the footer hint, the dark text plates where text sits on something busy. If John's `menu_background.565` is on the board it still wins over the style (D-007); the style is what shows without it.

## Options
### A. Casino felt and chips (recommended)
- **Background:** a green felt with a soft vertical shade (60 horizontal `fill_rect` strips, 4 rows each, from `rgb(0, 70, 30)` at the top to `rgb(0, 100, 45)` at the bottom), a double gold border 4 px in from the edge, and a faint cream diamond pattern across the title band.
- **Title:** "Pocket Chance" in gold size-2 with a 1 px black drop shadow; the chips figure under it on a cream plate shaped like a casino plaque (a rounded rectangle: two `fill_rect` plus four quarter `ellipse` corners).
- **Rows:** each row is a wide pill in that game's felt colour (DR-065: green for Blackjack, deep blue for Ultimate, burgundy for Caribbean, dark grey for Off): a rectangle with `ellipse` ends. Unselected pills are drawn 2 shades darker with white text; the selected pill is full colour with a gold outline and cream text, and a small gold chip (a 12 px filled `ellipse` with a white ring) sits at its right end as the cursor.
- **Icon slot:** until John's icons exist, a code-drawn suit sign in cream: a spade for Blackjack (two ellipses and a small triangle via `poly`), a diamond for Ultimate (`poly`), a club for Caribbean (three ellipses and a stem), a power sign for Off (a ring and a bar).
- **Cost estimate:** the shade is 60 `fill_rect` calls (about 1 ms), the pills and suits a few dozen primitives (about 5 ms), text as today, one `show()` 18.5 ms; entry about 40 ms, a joystick move two band pushes as today (the shade is redrawn per band from its row index, so no buffer). RAM: 2.6 KB of code and constants measured (HR-072), boot 65.7 KB free instead of 68.0; no buffers.
- Pros: looks like the games; ties the per-game felt colours (DR-065) into the menu so John knows which door he is opening.
- Cons: a gradient of 15 shades is as smooth as 16-bit colour on this panel gets; a 1 px banding is visible up close.

### B. Neon marquee
- **Background:** black. A rectangle of 24 "bulbs" (6 px filled `ellipse`) around the edge; every 150 ms the lit bulb steps one place (a chase), drawn as a 12-row band push at the top and bottom edges and two 12-column side strips via the scratch buffer.
- **Title:** "POCKET CHANCE" in alternating gold and white letters, size 2; the chips in white below.
- **Rows:** labels in white size-2 with a magenta chevron cursor; the chosen row gets a thin two-colour frame (cyan outside, magenta inside).
- **Cost estimate:** the chase is a 4 ms push every 150 ms, so the menu loop never idles; the sides need `show_rect` (7 ms each); CPU and backlight stay busy while John reads the menu. Zero RAM beyond the bulb index.
- Pros: the liveliest; reads as "casino" from across the room.
- Cons: constant drawing in a screen that should be quiet (power when the battery exists, DR-PCB); clashing colours on a small panel; the per-game colours cannot show.

### C. Card fan
- **Background:** dark green felt (flat), a single gold border.
- **Rows:** a cream card panel (rounded rectangle) per row with the label in black; the chosen panel is lifted 2 px and framed in gold.
- **Icon slot:** two code-drawn mini cards (20 x 28, cream with a red or black rank) fanned at 10 degrees: A-K for Blackjack, A-A for Ultimate, 4-4 for Caribbean (the dealer's qualifying pair), a face-down pair for Off. The mini cards are 6 primitives each.
- **Cost estimate:** entry about 35 ms; a joystick move as today. Zero RAM beyond constants.
- Pros: calm and readable; the mini cards tell the games apart without icon art.
- Cons: the fan needs a rotated rectangle, which `framebuf` has not got: it is approximated with `poly`, and at 20 px the second card looks jagged; cream panels on a 240 px screen leave little felt showing.

## Recommendation
Option A. It is the cheapest to draw well on this panel (no rotation, no animation), it reuses the per-game colours John has just approved, and John's icons and his photo both drop in unchanged. What would change my mind: if John wants movement on the menu, B, after the expert measures the chase against the battery figures.

## What John would have to do or accept
Nothing to draw. Pick A, B or C, or say what he has in mind (a photo of a real menu he likes helps me more than words). The expert measures the chosen style's entry redraw and band pushes before it is uploaded.

## Appendix
Today's menu: `pocket.py` (`draw_menu`, `draw_row`, `menu_select`), `ROW_Y = (70, 118, 166)`, rows 208 x 48 at x 16, plates `PLATE = rgb(8, 10, 18)`, background `BG = rgb(10, 20, 30)`. Measured: entry 92 to 104 ms with the photo (HR for D-007), 124 ms with the five-row scroll (DR-022 bench), joystick move 45 to 63 ms, 66.8 KB free after. Every style above keeps the same geometry, so `tests/test_screens.py` and the text-bounds test stay valid.
