# Upload list

_Kept current by the senior dev. Upload in the order shown using Viper IDE, then run the test line._

**Last updated:** 2026-10-04

## Board state right now
The old `main.py` was erased at your request (ruling D-003), so **the board boots to a blank screen** until a new program is installed. Nothing is lost: the old program is `main_monolith.py` in this repo and `backups/2026-10-03/main.py`.

The new game does **not** replace `main.py` yet (ruling DR-001). It installs as `/pocket.py` and you run it by hand from Viper IDE. Making it start at boot is step 3 below, and only after you have seen it run.

## Step 1: first upload of the new game
The expert ran this build on the bench on 2026-10-04 (8 scripted hands, no errors, 64 KB RAM free) after fixing one start-up bug (HR-F02). Awaiting a re-bench of the fixed files before you upload.
Create these folders on the board if they do not exist: `/lib`, `/games`, `/assets`.

| # | From this repo | To the board |
|---|---|---|
| 1 | `lib/pixfmt.py` | `/lib/pixfmt.py` |
| 2 | `lib/clocks.py` | `/lib/clocks.py` |
| 3 | `lib/lcd.py` | `/lib/lcd.py` |
| 4 | `lib/font.py` | `/lib/font.py` |
| 5 | `lib/buttons.py` | `/lib/buttons.py` |
| 6 | `lib/art.py` | `/lib/art.py` (not `assets.py`: the `/assets` folder would hide it, HR-F02) |
| 7 | `lib/save.py` | `/lib/save.py` |
| 8 | `lib/bankroll.py` | `/lib/bankroll.py` |
| 9 | `lib/cards.py` | `/lib/cards.py` |
| 10 | `games/blackjack_rules.py` | `/games/blackjack_rules.py` |
| 11 | `games/blackjack_table.py` | `/games/blackjack_table.py` |
| 12 | `games/blackjack.py` | `/games/blackjack.py` |
| 13 | `pocket.py` | `/pocket.py` |

Then, in Viper IDE, open `/pocket.py` on the board and press Run.

**Test line:** the menu appears (title "Pocket Chance", `$1000`, Blackjack / Slots (soon) / Off). Joystick up/down moves the gold box, A opens Blackjack, joystick changes the bet, A deals, A hits, B stands, X doubles. Cards are plain cream rectangles with the rank printed on them until the art exists. B at the betting screen returns to the menu.

**Please copy the text that Viper prints** (lines starting `RESULT`) into a message for the PM. They tell me how much memory is free and whether the clock fix ran.

If the screen stays dark or shows rubbish, press Stop, change the line `FAST_SPI = True` near the top of `/pocket.py` to `FAST_SPI = False`, run again, and tell the PM. That is the only known-unknown: the panel has not yet been looked at while running at full speed on the new firmware (HR-015).

## Step 1b: re-upload after John's play-tests (2026-10-04, second revision)
Three files changed after your feedback: the menu was laid out again (each highlight box now surrounds its own word), the bet line shows the doubled bet and takes the stake off the bankroll while a hand is in play, and the "You 21" line no longer has its lower half cut off (the screen is now four bands that never overlap).

| # | From this repo | To the board |
|---|---|---|
| 1 | `games/blackjack_table.py` | `/games/blackjack_table.py` |
| 2 | `games/blackjack.py` | `/games/blackjack.py` |
| 3 | `pocket.py` | `/pocket.py` |

**Test line:** menu rows are three boxed lines (Blackjack, Slots soon, Off), each word centred inside its box, nothing cut off. In blackjack, the "Dealer 17" and "You 21" lines are whole; after dealing, the top line shows your chips minus the bet; press X on your first two cards and the bet on the top line doubles, the total line says DOUBLED x2, and the result pays or takes twice the bet.

## Step 1c: splitting pairs (DR-016), 2026-10-04
Three files changed. Y splits a pair; the two hands sit side by side; the hand in play has a gold line under its total.

| # | From this repo | To the board |
|---|---|---|
| 1 | `games/blackjack_rules.py` | `/games/blackjack_rules.py` |
| 2 | `games/blackjack_table.py` | `/games/blackjack_table.py` |
| 3 | `games/blackjack.py` | `/games/blackjack.py` |

**Test line:** deal until you get a pair (two of the same rank, e.g. two 8s; a king and a jack do not count). The prompt shows "Y split". Press Y: the bet on the top line doubles, two hands appear side by side with the left one marked, A/B/X play the left hand then the right. The result line shows each hand, e.g. "WIN +10   LOSE -10". Two aces: Y deals one card to each and the round ends at once.

## Step 1d: menu background (D-007), 2026-10-04
_Optional, and the image is not in the repository: bring your own 240 x 240 `menu_background.bmp` (see `assets/src/ui/README.md`), convert it with `tools/convert_assets.py`, and upload the `.565` it writes. Without it the menu uses a plain dark colour._

John's casino photo behind the main menu. Two files.

| # | From this repo | To the board |
|---|---|---|
| 1 | `pocket.py` | `/pocket.py` |
| 2 | `assets/out/menu_background.565` | `/assets/menu_background.565` |

**Test line:** start `/pocket.py`: the photo fills the menu, the title, chips and footer sit on small dark plates, the selected row is a solid dark-blue box with a gold border, the other rows show the photo with a dark plate under the word. Joystick up/down moves the box with no flicker elsewhere. Without the `.565` file the menu is plain dark blue as before.

## Step 1e: scrolling menu for five games (DR-022), 2026-10-05
One file. The menu lists Blackjack, Slots, Caribbean, Hold'em and Off; three rows show at a time and a small gold arrow in the right margin says the list continues. The "soon" tag now sits under the word.

| # | From this repo | To the board |
|---|---|---|
| 1 | `pocket.py` | `/pocket.py` |

**Test line:** joystick down from Blackjack: Slots, then Caribbean (list scrolls when you pass the third row, a `^` appears top right), Hold'em, Off (`v` disappears). Up again to Blackjack. A on Blackjack still starts the game; A on a "soon" row does nothing.

## Step 1f: faster image loading (HR-F03), 2026-10-05
Two library files. The image loader now checks a file's size once and then goes straight to the pixels, which makes every card, chip and banner about 5 ms faster to draw. The screen driver gains a routine the slot reels will use.

| # | From this repo | To the board |
|---|---|---|
| 1 | `lib/art.py` | `/lib/art.py` |
| 2 | `lib/lcd.py` | `/lib/lcd.py` |

**Test line:** menu and blackjack look and behave exactly as before (with `table.565` present the felt still shows; without it the plain felt). The expert re-measures one card blit.

## Step 1g: slots (DR-017 to DR-023), 2026-10-05
Four files: three new game modules and the menu with Slots switched on. Runs with code-drawn stand-in symbols (coloured squares) until John's art exists; with `sym_*.565`, `cabinet.565` and `banner_jackpot.565` in `/assets` it uses them automatically.

| # | From this repo | To the board |
|---|---|---|
| 1 | `archive/slots/slots_rules.py` | `/games/slots_rules.py` |
| 2 | `archive/slots/slots_table.py` | `/games/slots_table.py` |
| 3 | `archive/slots/slots.py` | `/games/slots.py` |
| 4 | `pocket.py` | `/pocket.py` |
| 5 | `lib/art.py` | `/lib/art.py` (slots needs `open_sprite`, added after step 1f; the expert uploaded it during the bench) |

**Test line:** menu, Slots, A. The three reels scroll for about two seconds and stop left to right; the chips line shows the stake taken while they spin and the result after; a win shows "WIN +n" and the line name and blinks the gold frames three times. Joystick changes the bet (5 to 100), X shows the paytable, B returns to the menu. The first spin prints `RESULT slots mem_free mid-spin=...` (DR-020: expected about 45 to 50 KB; under 20 KB means fallback B is not enough and I need to know).

## Step 1h: sprite sheets (DR-024) and slots memory trims, 2026-10-05
Five files. The image loader learns sheets (one file per family of pictures, `assets/ASSETS.md`); blackjack and the menu open their sheets once per scene; the slot reels read rows from one open symbols file (no file opens during a spin). Slots also builds stand-in rows only for symbols without art, cleans up after start and prints `RESULT slots mem_free after init=...` beside the mid-spin line. With no sheet files in `/assets` everything behaves exactly as before (single files, then code-drawn).

| # | From this repo | To the board |
|---|---|---|
| 1 | `lib/sheets.py` | `/lib/sheets.py` (new; `art.py` imports it, so upload it first) |
| 2 | `lib/art.py` | `/lib/art.py` |
| 3 | `games/blackjack.py` | `/games/blackjack.py` |
| 4 | `archive/slots/slots.py` | `/games/slots.py` |
| 5 | `pocket.py` | `/pocket.py` |

**Test line:** menu, blackjack hand, slots spin all as before. Copy the `RESULT` lines to the PM, including both `slots mem_free` lines.

## Step 1i: slots removed (D-009), smaller libraries, 2026-10-05
Slots is dropped. The menu is Blackjack, Caribbean, Hold'em, Off. The libraries lose the slots code and a few KB of RAM (`sheets.py` no longer builds a name table at import; the screen driver and sheet reader no longer allocate per call). Blackjack and the menu are otherwise unchanged.

| # | From this repo | To the board |
|---|---|---|
| 1 | `lib/sheets.py` | `/lib/sheets.py` |
| 2 | `lib/art.py` | `/lib/art.py` |
| 3 | `lib/lcd.py` | `/lib/lcd.py` |
| 4 | `pocket.py` | `/pocket.py` |
| 5 | **delete** `/games/slots.py`, `/games/slots_rules.py`, `/games/slots_table.py` from the board | |

**Test line:** menu shows four rows (no Slots); blackjack plays as before. Copy the `RESULT` lines (boot and blackjack mem_free) to the PM.

## Step 1j: Caribbean Stud (DR-025 to DR-032), 2026-10-05
Seven files: the poker hand evaluator (new on the board; `stud_rules.py` imports it, so upload it first), three new game modules, the pays/strategy screen, the sheet list (one more banner) and the menu with Caribbean switched on.

| # | From this repo | To the board |
|---|---|---|
| 1 | `lib/poker.py` | `/lib/poker.py` (new; needed by `stud_rules.py`) |
| 2 | `lib/sheets.py` | `/lib/sheets.py` |
| 3 | `games/stud_rules.py` | `/games/stud_rules.py` |
| 4 | `games/stud_table.py` | `/games/stud_table.py` |
| 5 | `games/stud_pay.py` | `/games/stud_pay.py` |
| 6 | `games/stud.py` | `/games/stud.py` |
| 7 | `pocket.py` | `/pocket.py` |

**Test line:** menu, Caribbean, A deals: your five cards face up, the dealer's first card up and four face down, "Dealer shows K" and "You: pair of 9s" lines. A raises (the top line shows "ante 10 + 20"): the dealer's cards turn over one at a time about a third of a second apart, then the result banner and a line like "+30: ante + raise 20 x 1". B folds (all dealer cards shown at once, "-10: ante lost"). X shows the pays and the basic strategy. Copy the `RESULT` lines to the PM.

## Step 2: art (any time after step 1j)
On the Mac, from the repo folder:

```bash
python3 tools/convert_assets.py
```

It converts every BMP/PNG under `assets/src/`: single pictures (`table`, `menu_background`, `logo`) to `assets/out/<name>.565`, and packs each family (cards, chips, banners, icons) into one sheet file (`assets/out/cards.565` etc., see `assets/ASSETS.md`). Pictures not drawn yet become transparent placeholders inside their sheet and are listed. Wrong sizes or names are errors. Light or busy text zones on `table`, `cabinet` and `menu_background` print a WARNING.

| # | From this repo | To the board |
|---|---|---|
| 1 | `assets/out/<name>.565` (each file the converter wrote or re-wrote) | `/assets/<same name>.565` |

**Test line:** start `/pocket.py`; blackjack shows the drawn cards and chips where they exist. Nothing to change in the code. (`tools/pilot_test.py` still works for the single table image and prints timings; it reads `c_AS`, `c_back` and `chip_5` as single files only, so with sheets it will report them as missing: that is expected.)

## Step 3: start at boot (only when you are happy with step 1)
Upload `pocket.py` a second time, named `/main.py` on the board. Unplug and plug in: the menu should appear by itself. This overwrites the boot file, so it is your call, not mine.

## Not run anywhere yet
All of this has run only on the Mac, against stand-in `machine` and `framebuf` modules (96 tests). Nothing has run under MicroPython or on the board. Timing, colours on the panel and RAM use are what step 1 finds out.

## On the board now (code, after step 1j)
_The record of what the board holds. `tools/check_upload.py` reads it: every module a board file imports must be here, every method a board file calls on the shared libraries must exist in the version recorded here, and a repo file that differs from its recorded version is flagged as not yet uploaded. After an upload, run `python3 tools/check_upload.py --record <step> <repo paths...>` to update the rows._

| Board path | Repo file | Step | Version (git blob) |
|---|---|---|---|
| `/lib/poker.py` | `lib/poker.py` | 1j | 41fea1368c8c |
| `/games/stud.py` | `games/stud.py` | 1j | 474f431e179b |
| `/games/stud_pay.py` | `games/stud_pay.py` | 1j | 36fde234415a |
| `/games/stud_table.py` | `games/stud_table.py` | 1j | fe06c8a6ac90 |
| `/games/stud_rules.py` | `games/stud_rules.py` | 1j | 3aa5af7c4a7e |
| `/lib/sheets.py` | `lib/sheets.py` | 1j | e3adeacc4c38 |
| `/pocket.py` | `pocket.py` | 1j | d72d5918b2fc |
| `/lib/pixfmt.py` | `lib/pixfmt.py` | 1 | 03010786bfba |
| `/lib/clocks.py` | `lib/clocks.py` | 1 | b8c0bbf5c8f0 |
| `/lib/lcd.py` | `lib/lcd.py` | 1i | 3c6b0dee4cfc |
| `/lib/font.py` | `lib/font.py` | 1 | 7b1a40a2df70 |
| `/lib/buttons.py` | `lib/buttons.py` | 1 | 7dd47cbb1e2e |
| `/lib/art.py` | `lib/art.py` | 1i | 9031232c4b05 |
| `/lib/save.py` | `lib/save.py` | 1 | 4abeb7ea2133 |
| `/lib/bankroll.py` | `lib/bankroll.py` | 1 | be0756d4beef |
| `/lib/cards.py` | `lib/cards.py` | 1 | 117c3004184b |
| `/games/blackjack_rules.py` | `games/blackjack_rules.py` | 1c | 6000c8ab25fd |
| `/games/blackjack_table.py` | `games/blackjack_table.py` | 1c | 47214b7e2d74 |
| `/games/blackjack.py` | `games/blackjack.py` | 1h | b9ee6035a735 |

Also on the board: `/assets/menu_background.565` (step 1d), `/save.json` and `/save.bak` (written by the game). The old `main.py` is gone (D-003). The three `/games/slots*.py` files are deleted at step 1i (their code is in `archive/slots/`).

## Not on the board yet
Nothing at the moment.

## Restore the old version
Upload `main_monolith.py` and name it `/main.py` on the board.
