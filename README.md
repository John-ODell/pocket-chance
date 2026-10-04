# Pocket Chance (J'Boy)

A pocket casino for a Raspberry Pi RP2040 board with a 1.3" 240x240 screen, written in MicroPython. It runs offline. Blackjack is playable now. Slots is being built. Caribbean Stud and Ultimate Texas Hold'em come after that.

**Last updated:** 2026-10-04

---

# PART 1. Put the game on your board (no experience needed)

> **There is no Android app or APK in this project.** This is a game that runs on a small circuit board. "Installing" it means copying files onto the board over a USB cable. This part shows how.

## What you need
- [ ] The board (Waveshare RP2040-Plus) with the screen HAT on it
- [ ] A USB-C **data** cable (a charge-only cable will not work)
- [ ] A Mac with Chrome
- [ ] This folder: `pico-pocket-chance`

## Before you start (the one thing that trips everyone up)
- Only **one program** can talk to the board at a time. Viper IDE (a website you use in Chrome) and the terminal tools both want it.
- If the board does not show up, close the Viper tab, or quit Chrome with **Cmd+Q**, then try again.
- Never hold the **BOOTSEL** button while plugging in unless you mean to reinstall the firmware. Normal use: just plug in.

## Step 1: Plug in the board
- [ ] Plug the USB-C cable into the board and into your Mac.
- [ ] The screen may stay **dark**. That is normal. The game does not start by itself yet (see Step 5).

## Step 2: Open Viper IDE
- [ ] Open Chrome.
- [ ] Go to **viper-ide.org**.
- [ ] Click the connect button and choose the board when Chrome asks. (It may show up as "MicroPython" or "Board in FS mode".)
- [ ] When it connects you can see the files on the board.

## Step 3: Copy the files onto the board
The exact, always-current list lives in [`UPLOAD.md`](UPLOAD.md). Follow that list. Here is what the board needs right now:

- [ ] Make three folders on the board: **`/lib`**, **`/games`**, **`/assets`**
- [ ] Copy each file from this folder to the same place on the board:

| From this folder | To the board |
|---|---|
| `lib/pixfmt.py`, `clocks.py`, `lcd.py`, `font.py`, `buttons.py`, `art.py`, `save.py`, `bankroll.py`, `cards.py` | `/lib/` |
| `games/blackjack_rules.py`, `blackjack_table.py`, `blackjack.py` | `/games/` |
| `pocket.py` | `/pocket.py` (top level) |
| `assets/out/menu_background.565` | `/assets/menu_background.565` |

- [ ] **Do not** copy `lib/poker.py` or the slots files yet. They are not finished.
- [ ] Do **not** rename `art.py` to `assets.py`. The `/assets` folder would hide it and the game would not start.

## Step 4: Run it
- [ ] In Viper, open **`/pocket.py`** on the board.
- [ ] Press **Run**.
- [ ] You should see: your casino photo, the title "Pocket Chance", your chips (`$1000` at first), and a menu.

If the screen stays dark or shows garbage:
- [ ] Press **Stop**.
- [ ] Open `/pocket.py` and change `FAST_SPI = True` to `FAST_SPI = False` near the top.
- [ ] Run again, and tell the PM what you saw.

## Step 5 (optional): Make it start by itself
Right now you press Run each time. To make the menu appear whenever the board is plugged in:
- [ ] Copy `pocket.py` to the board a second time and name it **`/main.py`**.
- [ ] Unplug and plug in again. The menu should appear on its own.

## Going back to the old game
- [ ] Copy `main_monolith.py` to the board and name it **`/main.py`**.

## The controls
Landscape, with USB-C and the joystick on the left, and the buttons on the right.

| Where | Control | Does |
|---|---|---|
| Menu | Joystick up / down | Move the box (the list scrolls) |
| Menu | **A** | Pick the highlighted game. "Off" stops the program. Games marked "soon" do nothing yet |
| Blackjack, betting | Joystick up / down | Change the bet (5 to 500, steps of 5) |
| Blackjack, betting | **A** deal, **B** back to menu | |
| Blackjack, playing | **A** hit, **B** stand, **X** double, **Y** split a pair | |

## If something goes wrong
| What you see | What to do |
|---|---|
| The board does not show up in Viper | Another program has it. Close other Viper tabs and quit Chrome (Cmd+Q), then reopen. Check the cable is a data cable |
| Dark screen after Run | `FAST_SPI = False` (Step 4) |
| "no module named ..." | A file is missing or in the wrong folder. Check Step 3 |
| Menu says Off and the screen stops | Normal: "Off" ends the program. Unplug and plug in, then Run again |
| You pressed Stop and nothing is running | Run `/pocket.py` again |

---

# PART 2. Where the project stands

## What works today
- **Blackjack** is fully playable on the board: bet, deal, hit, stand, double, **split pairs**, result banners, "Shuffling" at the cut card, an out-of-chips refill, and a saved bankroll.
- **Menu** with your casino photo, a scrolling five-item list, and dark plates so the text stays readable.
- **Your chips are saved** to the board after every finished hand (with a backup copy and recovery if the save is damaged).
- **Full-speed screen:** a clock fix brings the screen link back to 62.5 MHz (about 58 frames a second for a full redraw).
- All art is drawn in code for now (plain cream cards, felt colour). Your real art plugs in as it arrives.

## What is in progress
- **Slots** is being built. The engine and the odds are done and tested. The screens are in progress.
- **Caribbean Stud**, then **Ultimate Texas Hold'em**, come after slots. A shared poker hand evaluator is already written and tested (`lib/poker.py`).

## The rules we chose (all approved by John)
| Game | Rules | House edge |
|---|---|---|
| Blackjack | 6 decks, reshuffle at 75% dealt, dealer stands on all 17, blackjack pays 3:2, hit/stand/double, split pairs once (aces one card each, double after split OK) | about 0.55% |
| Slots | 3 reels, one centre line, 8 symbols, bets 5 to 100, jackpot 1000x for three stars, one-cherry returns your bet | return 93.84%, a win about 1 spin in 3.6 |
| Chips | Start with 1000. Free refill when you are broke | n/a |

## What the screen can do (measured on the board)
| | |
|---|---|
| Full redraw | about 17 ms (58 fps) with the clock fix |
| Redraw one band | about 15 to 55 ms |
| RAM free while playing | about 50 to 70 KB of 264 KB |
| Flash for files | about 15 MB free |
| One save | about 55 to 150 ms, once per round |

## Your art: what is needed
| Need | Status |
|---|---|
| Menu photo | **Done** |
| Table background (240 x 240) | Optional, not made yet |
| 4 pilot images: `c_AS`, `c_back`, `chip_5`, `table` | Not made yet. Waiting on a decision about card file format (see below), so **hold off on cards** |
| Slot symbols: `sym_cherry`, `sym_star`, `sym_bar` first, then lemon, orange, bell, seven, diamond | Ready to start any time. 56 x 56, 24-bit BMP, no magenta |
| Slot cabinet (240 x 240, optional) and jackpot banner (200 x 40) | After the symbols |
| All the rest of the card art (53 cards) | After the pilot |

Exact sizes, names, text-safe zones and rules: [`assets/ASSETS.md`](assets/ASSETS.md). Put source files in `assets/src/<folder>/`, then run `python3 tools/convert_assets.py` on the Mac.

## Open decisions
- Card art file format: the board takes about 3 ms just to open any file, so cards stored one per file would draw slower than the plain code-drawn ones. The fix is to pack all 53 into one file (you still draw 53 separate images). The dev is writing this up for a ruling.
- Starting the game at boot (renaming `pocket.py` to `main.py`): your call, whenever you like.

---

# PART 3. Reference

## Hardware (all verified on the board)
| Part | Notes |
|---|---|
| Board | Waveshare RP2040-Plus, 16 MB flash, 264 KB RAM, USB-C. Running MicroPython v1.29.0 (the 16 MB build). About 15 MB of flash is usable for files |
| Screen | Waveshare Pico LCD 1.3" (ST7789, 240 x 240, SPI1). Colour is big-endian RGB565. Upright landscape |
| Inputs | 4 buttons and a 5-way joystick, all active-low, no contact bounce seen |

| Function | GPIO |
|---|---|
| LCD DC / CS / SCK / MOSI / RST / BL | 8 / 9 / 10 / 11 / 12 / 13 |
| Buttons A / B / X / Y | 15 / 17 / 19 / 21 |
| Joystick up / down / left / right / press | 2 / 18 / 16 / 20 / 3 |

Which physical button (top to bottom) is A, B, X and Y is still unconfirmed. The code uses the pin numbers, so it plays correctly either way.

## Repository layout
```
pocket.py          the game's start file on the board (menu)
main_monolith.py   the old program (restore point, read-only)
lib/               shared modules for the board (screen, fonts, buttons, images, saving, cards, clocks, poker)
games/             one set of modules per game (rules, table logic, screens)
assets/ASSETS.md   art spec: sizes, formats, names, text-safe zones
assets/src/        your source art    assets/out/   converted files for the board
tools/             Mac-side tools: image converter, odds simulators, upload checker
tests/             automated tests (run on the Mac, no board needed)
hw/ hwtest/        hardware measurements, board notes, benchmark scripts
backups/           copies of what was on the board before every change
pm/                decisions, rulings, status, hand-off notes
UPLOAD.md          the exact upload list, step by step
CLAUDE.md          rules for the AI sessions working here
```

## Running the tests
```bash
python3 -m unittest discover -s tests
```
173 tests pass at the latest commit. They run on a Mac with stand-in modules for the board.

## How the project is run
| Role | Who | Does |
|---|---|---|
| Owner | John | Makes the art, tries things on the board, approves decisions |
| PM | Claude session "The PM" | Routes decisions, tracks scope, texts John for actions |
| Senior dev | Claude session | Writes and tests the software, files decision requests |
| Hardware expert | Claude session | Measures the board, uploads builds, reviews anything touching speed, memory, storage or power |

Decisions flow as files: the dev files `pm/inbox/DR-NNN-*.md` with one recommendation, the expert reviews hardware-related ones in `hw/reviews/`, the PM takes them to John and records the ruling in `pm/outbox/`, and every ruling is listed in [`pm/DECISIONS.md`](pm/DECISIONS.md). Details: [`pm/README.md`](pm/README.md).

## Credits
The display driver and font in `main_monolith.py` are adapted from Tony Goodhew's Waveshare 1.3" workout (August 2021). Waveshare datasheets and demo code are kept outside this repository. MicroPython firmware for the board is a public download and is not stored here.
