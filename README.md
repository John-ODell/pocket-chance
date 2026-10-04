Pocket Chance (J'Boy) - John O'Dell

A pocket casino for the Waveshare RP2040-Plus and the Waveshare 1.3" LCD HAT, written in MicroPython. It runs offline on the board. Three games: Blackjack, Ultimate Texas Hold'em and John's own Caribbean, a flop game with a low or high call.

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
| Ultimate, betting | Joystick, **A** deal, **X** help, **B** menu | Blind equals the Ante |
| Ultimate, pre-flop / flop / river | **A** raise (4x / 2x / 1x), **Y** raise 3x pre-flop, **B** check (fold at the river) | The table cards turn as you go; the river prompt shows the dealer outs |
| Caribbean, betting | Joystick up / down, left / right | Change the Ante (5 to 50, capped at a fifth of your chips) |
| Caribbean, betting | **A** deal, **X** help, **B** menu | |
| Caribbean, flop | **A** call high (4x the Ante), **Y** call low (2x), **B** fold | The last two table cards turn, then the dealer's cards one by one |

## Games

| Game | Status | Rules | House edge |
|---|---|---|---|
| Blackjack | **Playable** | 6 decks, reshuffle at 75% dealt, dealer stands on all 17, blackjack pays 3:2, hit / stand / double, split pairs once (aces get one card each, double after split allowed) | about 0.55% |
| Ultimate Texas Hold'em ("Ultimate") | **Playable** | Equal Ante and Blind (5 to 50), two hole cards, five table cards; raise 4x or 3x pre-flop, 2x after the flop, 1x at the river or fold; dealer needs a pair for the Ante to count; Blind pays straight 1:1 up to royal 500:1. X teaches the full published simple strategy and the river prompt shows the dealer-outs count (`UTH_HINT`). Four other players sit at the sides as chip stacks (`UTH_SEATS`) | about 2.4% of the ante with the taught strategy, 2.2% optimal |
| Caribbean (John's flop game) | **Playable** | Ante 5 to 50, two cards each, the first three table cards turn, then call high (4x) or low (2x) or fold, the last two turn; best five of seven; the dealer needs a pair of fours or better, otherwise every bet pushes; a winning Ante pays by a table (flush 2:1, full house 3:1, quads 10:1, straight flush 20:1, royal 100:1, else 1:1), the call 1:1. When you and all four seats beat a dealer hand, a win on the next hand pays three times (Ante and call together). Four chip-stack seats (`CAR_SEATS`). The published game this is based on is Casino Hold'em (one call size, 2.16% optimal) | about 5% of the ante with the taught strategy (15% without the multiplier) |
| Caribbean Stud | Archived (John's ruling, 2026-10-06) | Was on the board as "Caribbean" until step 1n; code in `archive/stud/` | 5.2% |
| Slots | Shelved | A 3-reel machine was built and tuned (93.84% return) then dropped: a classic multi-line machine does not fit the board's RAM. Code kept in `archive/slots/` | n/a |

Chips: you start with 1000. If you go broke you get a free refill. Your chips are saved to the board after every round, with a backup copy and recovery if the save is damaged.

The house edges were measured by simulation (`tools/bj_edge.py`, `tools/bj_split.py`, `tools/uth_edge.py`, `tools/casino_holdem_edge.py`; `archive/stud/stud_edge.py` for the archived game) and the rules were checked against the public references on wizardofodds.com.

## What it does well on this hardware
- Full-speed screen: about 58 frames a second for a full redraw, once the board's peripheral clock is set from the system PLL (one `machine.freq` call at the top of `pocket.py`, see `docs/HARDWARE.md`).
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
pcb/               workspace for designing your own board from this hardware (first-timer guide, in progress)
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
