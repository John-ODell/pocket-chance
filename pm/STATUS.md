# Status

_Updated by the senior dev at the end of each session. Written for John._

**Last updated:** 2026-10-04 (night)

## Where we are
Every decision for Phase 1 is approved (DR-001 to DR-015) and the first full version of the game is written. **It has never run on the board.** I have asked the expert to look it over on the bench first; after that the next step is yours: upload it following `UPLOAD.md` step 1 and tell the PM what you see.

The board currently boots to a blank screen because the old program was erased at your request (D-003). The new game installs as `/pocket.py` and you start it by hand from Viper IDE; it does not take over the boot file until you say so (`UPLOAD.md` step 3).

## Splitting pairs is built (DR-016, approved)
Y splits a pair of the same rank into two hands, each with its own bet (the bankroll must cover the second bet). The two hands sit side by side; a gold line marks the one you are playing. Aces get one card each and stand. You can double after a split. A 21 after a split pays even money. The result line shows both hands. 25 new tests cover the engine, the table and the screen, and the text test now checks the split layouts too. House edge drops to about 0.55%. Files to upload are in `UPLOAD.md` step 1c; the expert can do it.

## Your first play (2026-10-04) and what I did about it
- **"Double seems off":** the arithmetic was right (the expert confirmed it on the bench: bet doubled, one card, balance moved by exactly twice the bet). What was wrong is what you saw: the top line kept showing the original bet, and nothing said the hand had been doubled. Now the top line shows your chips minus the stake while a hand is in play, the bet doubles on screen when you press X, the total line says "DOUBLED x2", and the result line reads "DOUBLED: bet 20, +20". 16 new tests cover every step of the double path. If you saw something else, tell the PM what happened and I will chase it.
- **Split:** not in v1 by your earlier ruling (DR-012). I filed **DR-016** recommending split once, any pair, aces one card each, double after split allowed; it lowers the house edge from about 0.97% to about 0.55% (measured, 3 million hands per row). Y would be the split button.
- **"Main select screen is a mess":** confirmed. "Slots (soon)" was drawn 44 px off the right edge and the labels crossed the highlight box. The menu is laid out again (three boxed rows, labels inside the rows, "soon" small and grey) and a test now measures every string on every screen against the 240 px panel, so this cannot come back. A photo of the new menu after you re-upload would help me confirm it looks right.
- **"You: total" line cut off at the bottom:** found and fixed. The player area ended 4 px above where the text ended, so the next area painted over it. The screen is now four bands that never overlap, and the text test also checks that every line's pixels survive a full redraw, so nothing can paint over a line again.
- **Highlight box far to the right of the word:** in the new menu each word is centred inside its own box, and a test checks the centring and that the box is on screen.
- **"Just text on black, looks very bad":** noted and agreed. This is the placeholder look until your art arrives; the clean-up pass comes after the pilot images, not now.
- Re-upload is `UPLOAD.md` step 1b (three files); the expert can do it.

## Bench check result (expert, 2026-10-04)
The expert ran the build on the board. One blocker, now fixed: the image-loader module was called `assets.py`, and on the board the empty `/assets` folder hid it, so the game would not start. It is renamed `lib/art.py` (a file rename within DR-001, no new decision). A test now fails if any module is ever named like a board folder. Everything else was good: 8 scripted hands with no errors, a full redraw in about 43 ms, bet change 15 ms, hit 29 ms, 64 KB of RAM free after play. I also moved the save to after the result is drawn, so the banner appears instantly instead of up to 0.18 s later. The expert is re-checking the fixed build before you upload.

## Done today
- **Screen, buttons, clock fix, image loader, saving:** the shared modules in `lib/`. The clock fix from DR-015 is in `lib/clocks.py` with the `FAST_SPI` switch at the top of `pocket.py`.
- **Blackjack screens** (`games/blackjack.py`): bet with the joystick, A deals, A hits, B stands, X doubles, "Shuffling..." when the shoe is reshuffled, result banner, out-of-chips screen with the free 1000. Everything draws with plain code shapes when an image is missing, so the game plays before any art exists.
- **Menu** (`pocket.py`): Blackjack, Slots (marked "soon"), Off. Shows your chips. Loads the blackjack code only when you pick it and frees it after.
- **Saving:** your chips are written to `/save.json` after every finished hand, with a backup copy, exactly as DR-007 and DR-008 say. If the file is ever damaged you will see a one-line message at start-up.
- **Image converter** (`tools/convert_assets.py`): turns your BMP/PNG files into `.565` files for the board, checks sizes and names, and refuses wrong ones with a clear message.
- **Pilot board test** (`tools/pilot_test.py`): draws your four pilot images and prints timing and memory numbers.
- `assets/ASSETS.md` is updated to the approved format, with "which way up" and the pilot-first instruction. `chip_1` is now optional.
- **96 automated tests pass** on the Mac, including a headless run of the whole screen code against stand-in `machine` and `framebuf` modules, and a 600-random-key test that tries to crash the blackjack screen.

## John needs to upload or test
1. **`UPLOAD.md` step 1** (after the expert's bench check): upload 13 files, run `/pocket.py`, play a hand, copy the `RESULT` lines to the PM. If the screen is dark or garbled, flip `FAST_SPI` to `False` and tell the PM.
2. **Art:** make the four pilot images (`c_AS`, `c_back`, `chip_5`, `table`) at the sizes in `assets/ASSETS.md`, drawn the right way up as described there. Then `UPLOAD.md` step 2.
3. Nothing else is waiting on you.

## Your menu background (D-007)
Your casino photo is behind the main menu. Because the middle of the photo is bright (the lights), the words sit on small dark plates and the selected row is a solid dark-blue box, so everything stays readable; the photo shows in the margins and inside the other rows. Moving the joystick redraws only the two rows that change. The converter warned that the top strip and the first row are bright, which is why the plates are there. Files for the expert: `UPLOAD.md` step 1d (`pocket.py` and `assets/out/menu_background.565`).

## Your table background
You said you want to draw the felt yourself. `assets/ASSETS.md` now has a "Readability" section with the exact pixel boxes where text and cards sit, so you know which areas to keep dark and calm. The converter warns (but still converts) if a text area of your table is too light or busy. Upload just `assets/out/table.565` and the game uses it at the next start; no code changes.

## Waiting on a decision
Nothing. I will file a request before any new work on slots (Phase 2), and for making `pocket.py` the boot file if you prefer it decided here rather than in `UPLOAD.md`.

## What I plan next
- Fix whatever the bench check and step 1 turn up.
- A `tools/check_upload.py` that checks the files on the Mac match the upload list (sizes, compile), so uploads are less error-prone.
- Then slots, after a scope request.

## Not tested, honestly
- Nothing has run under MicroPython or on the board. The CPython stand-ins mimic `framebuf` and `machine` but cannot catch MicroPython-only differences, timing, or how the panel looks.
- The panel has not been looked at while running at the full 62.5 MHz on the new firmware. That is why `FAST_SPI` exists.
- Real RAM use after all modules load. `pocket.py` prints it (`RESULT boot mem_free=...`) so step 1 answers it.
- Scaled text (`font.py`) is drawn pixel by pixel in Python; it is only redrawn on button presses, which should be fine, but speed is unmeasured.
