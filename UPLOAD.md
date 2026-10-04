# Upload list

_Kept current by the senior dev. Upload in the order shown using Viper IDE, then run the test line._

**Last updated:** 2026-10-04

## Board state right now
The old `main.py` was erased at your request (ruling D-003), so **the board boots to a blank screen** until a new program is installed. Nothing is lost: the old program is `main_monolith.py` in this repo and `backups/2026-10-03/main.py`.

The new game does **not** replace `main.py` yet (ruling DR-001). It installs as `/pocket.py` and you run it by hand from Viper IDE. Making it start at boot is step 3 below, and only after you have seen it run.

## Step 1: first upload of the new game (nothing to test on the board has been run yet)
Create these folders on the board if they do not exist: `/lib`, `/games`, `/assets`.

| # | From this repo | To the board |
|---|---|---|
| 1 | `lib/pixfmt.py` | `/lib/pixfmt.py` |
| 2 | `lib/clocks.py` | `/lib/clocks.py` |
| 3 | `lib/lcd.py` | `/lib/lcd.py` |
| 4 | `lib/font.py` | `/lib/font.py` |
| 5 | `lib/buttons.py` | `/lib/buttons.py` |
| 6 | `lib/assets.py` | `/lib/assets.py` |
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

## Step 2: pilot image test (after you have made the 4 pilot images)
On the Mac, from the repo folder:

```bash
python3 tools/convert_assets.py
```

It writes `assets/out/c_AS.565`, `c_back.565`, `chip_5.565`, `table.565` and prints a line per file, or a clear error if a file is the wrong size or name.

| # | From this repo | To the board |
|---|---|---|
| 1 | `assets/out/*.565` (each file) | `/assets/<same name>.565` |

Then open `tools/pilot_test.py` in Viper IDE and **Run it without saving it to the board**.

**Test line:** the table background, an ace of spades and a card back side by side, a red chip below them, "PILOT TEST" at the top, "TOP-LEFT" small at bottom-left. Everything the right way up and the right colours. Copy the `RESULT` lines to the PM. After this, `pocket.py` uses the same images automatically.

## Step 3: start at boot (only when you are happy with step 1)
Upload `pocket.py` a second time, named `/main.py` on the board. Unplug and plug in: the menu should appear by itself. This overwrites the boot file, so it is your call, not mine.

## Not run anywhere yet
All of this has run only on the Mac, against stand-in `machine` and `framebuf` modules (96 tests). Nothing has run under MicroPython or on the board. Timing, colours on the panel and RAM use are what step 1 finds out.

## Restore the old version
Upload `main_monolith.py` and name it `/main.py` on the board.
