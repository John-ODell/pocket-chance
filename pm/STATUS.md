# Status

_Updated by the senior dev at the end of each session. Written for John._

**Last updated:** 2026-10-05 (night)

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

## Slots dropped (D-009): what changed
As you decided, slots is out. The code is parked in `archive/slots/` with a note; the menu is Blackjack, Caribbean, Hold'em, Off; the art list no longer mentions slot symbols or a cabinet. The sprite sheets stay for cards, chips, banners and icons. I kept the memory fixes the expert's slots bench taught us (no allocations in the screen driver and sheet reader, a slimmer sheet list), which help blackjack too. **Step 1i is on the board (2026-10-05, with your go).** The expert benched it first: 68 KB free at boot (65 before), about 54 KB free while playing blackjack, no leak, verdict fits. A full redraw is about 48 ms and a card from the new sheet format 3.4 to 3.9 ms, so your card art will make the game faster, not slower (key press to result 84 ms with a card sheet, 94 ms without). The sheet code costs about 7.6 KB more RAM than before sheets existed; that is the price of DR-024 and it fits.

**Screen clock done the supported way (DR-050), `UPLOAD.md` step 1l.** The register trick is gone; one standard MicroPython line at the top of `pocket.py` does the same, measured identical by the expert, and the board now reports its real screen speed. `FAST_SPI = False` still exists if the screen ever looks wrong. The expert checks it from his mounted copy before anything is uploaded.

**Caribbean Stud is on the board and you said it is good.** Hold'em and the chip-stack seats wait for your rulings; the expert has measured them all and they fit. The Hold'em help-screen question is settled in DR-042: our simulator now agrees with the published figure (2.8% of the Ante with the full simple strategy, 6.8% without its river rule), so I recommend teaching the full strategy and showing the dealer-outs count as a hint; the expert measured the hint at a quarter of a second on the board, so it fits while you look at the river cards. A small clean-up request, DR-050, replaces the screen-clock register trick with a supported one-line call the expert measured as identical.

**Other players as chip stacks (DR-041 for Stud, DR-044 revised for Hold'em).** As you described: no faces, no cards, just stacks that grow or shrink with a green or red marker after each hand. On Stud they sit in a thin rail along the bottom edge (the screen has no other room); on Hold'em in the side boxes as proper piles of chip art. Each seat gets real cards from the same deck and plays the basic strategy, so the results are honest and never touch your odds; their chips are not saved. Not built yet.

**Ultimate Texas Hold'em: eight requests filed (DR-042 to DR-049), nothing built yet.** Rules and Blind pays (house edge 2.2% of the Ante with expert play per the published reference; our own simulator of the published simple strategy still measures about 6.9%, which I have flagged as unexplained in DR-042 so you can decide what the help screen teaches), a nine-card layout with four side boxes for the other players, the AI players you asked for (four text boxes with a name, chips and what they did; they play the house with the same simple strategy and never touch your odds; cards never shown on this screen; a Stud retrofit as a later request), buttons (A raise 4x, Y 3x, B check/fold), Ante 5 to 50 so a hand never costs more than 300, how the cards turn, the save, and the label "Hold'em" with all art reused.

**Caribbean Stud is built (all eight rulings applied), `UPLOAD.md` step 1j, six files for the expert.** Ante with the joystick, A deals, A raises or B folds, the dealer's cards turn over one by one, result and chips saved; X shows the pays and the three ace-king rules in plain words. 42 new tests. Earlier note: Rules and paytable with a measured house edge (5.2% of the ante with good play, matching the published figure), the screen layout (two rows of five cards in the blackjack bands), buttons (A raise, B fold), ante 5 to 100 so a raise is always affordable, the dealer's cards turning over one by one, the save, the menu word, and the art (everything reused; one optional new banner). The poker hand evaluator is built and tested. I build as soon as the rulings land.

## Sprite sheets built (DR-024, approved), upload step 1h
Your pictures now travel to the board as one file per family: `cards.565` (all 53), `chips.565`, `banners.565`, `icons.565`, `symbols.565`. You still draw one BMP per picture; `python3 tools/convert_assets.py` packs them and lists what is missing (missing ones are transparent placeholders, so a few drawn cards already show). Why: the expert measured 3 ms to open any file on the board, so 53 card files would have made blackjack slower than the plain drawn cards; from a sheet a card takes 2.9 ms and the slot reels read rows in 0.26 ms. `assets/ASSETS.md` has the table of sheets. Five files for the expert in `UPLOAD.md` step 1h.

## Slots bench: one upload mistake, fixed; memory being watched
The expert found that `UPLOAD.md` step 1g left out `lib/art.py`, which slots needs (it gained a routine after step 1f). Without it the first spin crashed. The expert uploaded the right file; step 1g now lists it. To stop this happening again, `UPLOAD.md` now carries a record of exactly which version of each file is on the board, and the upload checker refuses when a board file calls something its library on the board does not have, or imports a module that is not there. Memory: the expert measured about 27 KB free in his harness after the slots screen starts, less than I expected; the game prints the real number after start and mid-spin. I trimmed what I could (stand-in symbol rows are built only for symbols without art, a memory clean-up after start). If the mid-spin number is under 20 KB I reduce further, as ruled.

## New request: DR-024, one image file per family instead of one per picture
The expert found that opening a file costs about 3 ms on the board, so your 53 card pictures as 53 files would make blackjack slower than the plain drawn cards. DR-024 proposes that the converter packs each family (cards, chips, banners, icons, slot symbols) into one file; you still draw separate BMPs exactly as before, and uploads get easier (one file instead of 53). Waiting for your ruling before you convert card art.

## Slots is built (step 1g, four files for the expert)
The slot machine plays: bet 5 to 100 with the joystick, A spins, the three reels scroll the real symbol strip and stop left to right about 0.4 s apart, the win line and amount appear, the chips are saved, and a win blinks the gold frames. X shows the paytable (93.8% return, one line). Until your symbol art exists the reels show coloured squares, one colour per symbol. Memory: the expert found my first plan (44 KB) would not fit next to the menu, so, as you ruled, the fallback is built: three 6 KB window buffers scrolled in place with the incoming symbol read row by row (18.8 KB). The first spin prints the free memory mid-spin for the expert.

## Slots animation: measured, redesigned, back with the PM
The expert timed my spin animation plan on the board and it was four times too slow (82 ms a frame). The reason was in my image loader: every picture drawn cost about 8 ms of file-system overhead before a single pixel was read. Two things followed:
- **The loader is fixed** (`UPLOAD.md` step 1f): the size check happens once per picture per boot and is remembered, so cards, chips and banners will all draw about 5 ms faster once your art arrives. No change to what you see.
- **DR-020 is revised** to the design the expert measured: the symbols stay in memory while the reels spin, each reel re-reads only the symbol scrolling in, and the windows are sent straight to the screen. Measured 13 ms a frame (76 fps) at full speed and 18 ms (56 fps) at the slow clock. It needs about 44 KB of memory while the slots screen is open, the tightest point in the project, so the first bench will check the headroom.
- **DR-021 is revised** with the order the expert asked for: result drawn, then saved, then the win blinks. One save per spin is harmless for the flash (thousands of times below any wear limit).

## Approved for slots (DR-017, 018, 019, 022, 023) and what I did
- `assets/ASSETS.md` Phase 2 is final: 8 symbols at 56 x 56, the optional cabinet with the window positions fixed, the jackpot banner, `sym_blur` dropped, and the dark zones to keep calm. **Pilot files first: `sym_cherry`, `sym_star`, `sym_bar`.**
- The converter knows all Phase 2 names and warns about light or busy text zones on the cabinet, and about a symbol name that is not one of the eight.
- The menu is now a scrolling list for five games (`UPLOAD.md` step 1e, one file). The two poker games show as **"Caribbean"** and **"Hold'em"**: the names in the ruling ("Carib. Stud", "Ult. Hold'em") are too wide for the label area at this text size (176 and 192 px against 152 available), so I used the longest forms that fit and told the PM. Say if you prefer other short names.
- Waiting on the expert for DR-020 (spin animation) and DR-021 (win display and save rate) before the slot screens are built.

## Slots: seven decision requests filed (DR-017 to DR-023)
You approved slots next (D-008). Before I build the screen I need your rulings on: the reel layout (one payline, three reels, 8 symbols); the paytable (I recommend 93.8% return to player, a win on 28% of spins, a 1000x jackpot about once in 32,768 spins; the numbers are exact, not estimates); bets (same chips, 5 to 100 a spin); how the reels spin and stop (the expert reviews the redraw cost); how wins are shown (gold frame, amount, jackpot banner, a paytable screen on X, no auto-spin); the menu for five games (a scrolling list); and the final Phase 2 art list (window positions fixed, `sym_blur` dropped). The slots engine itself is already built and tested (`games/slots_rules.py`); the rulings only set its parameters.

Also built, for the two poker games later: a poker hand evaluator (`lib/poker.py`, 5 to 7 cards) with tests. Not uploaded yet.

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
