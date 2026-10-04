# Status

_Updated by the senior dev at the end of each session. Written for John._

**Last updated:** 2026-10-04 (afternoon)

## Where we are
Every decision for Phase 1 is approved (DR-001 to DR-015) and the first full version of the game is written. **It has never run on the board.** I have asked the expert to look it over on the bench first; after that the next step is yours: upload it following `UPLOAD.md` step 1 and tell the PM what you see.

The board currently boots to a blank screen because the old program was erased at your request (D-003). The new game installs as `/pocket.py` and you start it by hand from Viper IDE; it does not take over the boot file until you say so (`UPLOAD.md` step 3).

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
