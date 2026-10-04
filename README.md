Pocket Chance (J'Boy) - John O'Dell

A pocket casino for the Waveshare RP2040-Plus and the Waveshare 1.3" LCD HAT, written in MicroPython. It runs offline on the board. Blackjack is playable today. Caribbean Stud is being built, then Ultimate Texas Hold'em.

The HAT plugs onto the board, so there is no wiring in this project. The pin map and everything we measured on a real board is in [`docs/HARDWARE.md`](docs/HARDWARE.md).

This project was built with a small team of AI sessions (a PM, a developer and a hardware expert) directing one person. How that works, with role files and starter prompts you can reuse, is in [`docs/AI_TEAM.md`](docs/AI_TEAM.md).

Last updated: 2026-10-04

## Items needed
- Waveshare RP2040-Plus (16 MB version)
- Waveshare Pico LCD 1.3" HAT (240 x 240 screen, joystick, 4 buttons)
- USB-C data cable
- A computer with Python 3.9 or newer

## Quick start
The full follow-along guide is [`SETUP.md`](SETUP.md). The short version:

1. Download the **16 MB** MicroPython firmware for the RP2040-Plus from micropython.org. Hold BOOTSEL, plug in, drag the `.uf2` onto the `RPI-RP2` drive.
2. `pip install mpremote pillow`
3. Copy the files to the board with `mpremote fs cp` (exact commands in `SETUP.md`, Step 4).
4. `mpremote run pocket.py`

You should see the menu: "Pocket Chance", your chips, and the games.

If the screen stays dark, open `pocket.py` and set `FAST_SPI = False`. That is the only board-specific setting (see `docs/HARDWARE.md`, "The one trap").

## Controls
Landscape, with USB-C and the joystick on the left and the buttons on the right.

| Where | Control | Does |
|---|---|---|
| Menu | Joystick up / down | Move the box (the list scrolls) |
| Menu | **A** | Pick a game. "Off" stops the program |
| Blackjack, betting | Joystick up / down | Change the bet (5 to 500, steps of 5) |
| Blackjack, betting | **A** deal, **B** back to menu | |
| Blackjack, playing | **A** hit, **B** stand, **X** double, **Y** split a pair | |

## Games

| Game | Status | Rules | House edge |
|---|---|---|---|
| Blackjack | **Playable** | 6 decks, reshuffle at 75% dealt, dealer stands on all 17, blackjack pays 3:2, hit / stand / double, split pairs once (aces get one card each, double after split allowed) | about 0.55% |
| Caribbean Stud | In progress | Ante, five cards each, dealer shows one, fold or raise 2x, dealer needs Ace-King or better, raise pays 1 to 100:1, no jackpot | about 5.2% of the ante with good play |
| Ultimate Texas Hold'em | Planned | Ante and Blind, check or raise 4x / 3x pre-flop, 2x after the flop, 1x after the river | about 2.2% of the ante with good play |
| Slots | Shelved | A 3-reel machine was built and tuned (93.84% return) then dropped: a classic multi-line machine does not fit the board's RAM. Code kept in `archive/slots/` | n/a |

Chips: you start with 1000. If you go broke you get a free refill. Your chips are saved to the board after every round, with a backup copy and recovery if the save is damaged.

The house edges were measured by simulation (`tools/bj_edge.py`, `tools/bj_split.py`, `tools/stud_edge.py`) and the rules were checked against the public references on wizardofodds.com.

## What it does well on this hardware
- Full-speed screen: about 58 frames a second for a full redraw, once the board's SPI clock is fixed (`lib/clocks.py`).
- Redraws only the strip of the screen that changed, so a button press answers in about 15 to 100 ms.
- About 50 to 55 KB of RAM left while playing, on a board with 264 KB.
- Art is optional. With no image files the game draws cards and the table in code.

## Your own art (optional)
Sizes, names, and where text sits on each screen are in [`assets/ASSETS.md`](assets/ASSETS.md). In short: draw one 24-bit BMP per picture, magenta (255, 0, 255) is transparent, run `python3 tools/convert_assets.py`, and copy the files it writes to `/assets/` on the board. The menu background is a full-screen 240 x 240 image you supply yourself (`assets/src/ui/menu_background.bmp`). None is included.

## Repository layout
```
pocket.py          the game's start file on the board (menu)
lib/               shared modules for the board: screen, fonts, buttons, images, saving, cards, clock fix, poker
games/             one set of modules per game: rules, table logic, screens
archive/           shelved work (slots)
assets/            art spec and the converter's input and output folders
tools/             Mac-side tools: image converter, odds simulators, upload checker
tests/             automated tests (run on a computer, no board needed)
hw/ hwtest/        measured hardware budget, board notes, reviews, and the benchmark scripts
docs/              hardware reference sheet, the AI team guide, role files
pm/                decision requests, rulings, decision log, hand-off notes
SETUP.md           follow-along install guide
UPLOAD.md          exact file list for the board, checked by tools/check_upload.py
CLAUDE.md          rules for the AI developer session (Claude Code loads it)
main_monolith.py   the original single-file program this project replaced (read-only)
```

## Running the tests
```bash
python3 -m unittest discover -s tests
```
They run on a normal computer with stand-in modules for the board.

## Troubleshooting
| What you see | What to do |
|---|---|
| The board does not show up | Use a data cable. Close Viper IDE and its tab: only one program can use the USB port at a time |
| Dark screen | `FAST_SPI = False` in `pocket.py` |
| "no module named ..." | A file is missing or in the wrong folder. Compare with `SETUP.md`, Step 4 |
| "could not enter raw repl" | The board is fine. Unplug it, or run `hwtest/unwedge.py` |

More in [`SETUP.md`](SETUP.md).

## Credits
- The screen driver and font in `main_monolith.py`, and the code adapted from it, started from Tony Goodhew's Waveshare 1.3" workout (August 2021).
- Rules and house edges were checked against the public pages on wizardofodds.com.
- MicroPython firmware is a public download from micropython.org and is not stored here.
- Waveshare datasheets and demo code are not included.

## Issues
Open an issue with the step you were on, what you saw, and the full terminal output. Please do not post anything private.
