# Pocket Chance (J'Boy)

A pocket casino for a Raspberry Pi RP2040 board with a 1.3" 240x240 LCD, written in MicroPython. Blackjack comes first, slots second. The board has no networking, so it is all offline.

This started as an old Pico project (one 900-line file with five small games). It is now a rebuild with real art, honest odds and a saved bankroll. The old program is kept as `main_monolith.py` and still runs on the board.

## Status

**Phase 1, blackjack: in progress.** The rules engine and betting logic are built and tested on a Mac (58 tests). Nothing new runs on the board yet. See [`pm/STATUS.md`](pm/STATUS.md) for the current state, [`UPLOAD.md`](UPLOAD.md) for what to put on the board, and [`pm/DECISIONS.md`](pm/DECISIONS.md) for every decision made so far.

## Hardware

| Part | Notes |
|---|---|
| Board | Waveshare RP2040-Plus, 16 MB flash (original Pico: 2 MB), 264 KB SRAM, USB-C, LiPo header |
| Screen | Waveshare Pico LCD 1.3" (ST7789, 240x240, SPI1) |
| Input | 4 buttons (A/B/X/Y) and a 5-way joystick, all active-low |

The original code ran on a plain Pico. The RP2040-Plus has not been confirmed to match. The expert is checking this (`hw/BOARD.md`).

| Function | GPIO |
|---|---|
| LCD DC / CS / SCK / MOSI / RST / BL | 8 / 9 / 10 / 11 / 12 / 13 |
| Buttons A / B / X / Y | 15 / 17 / 19 / 21 |
| Joystick up / down / left / right / press | 2 / 18 / 16 / 20 / 3 |

## Repository layout

```
main_monolith.py   the old working program (read-only, restore point for the board)
lib/               shared modules for the board (cards, bankroll, ...)
games/             one module per game
assets/ASSETS.md   art spec: sizes, formats, file names (John makes the art)
assets/src/        source art (BMP/PNG)    assets/out/  converted files for the board
tools/             Mac-side tools: house-edge simulator, board probe
tests/             CPython unit tests for the game logic (python3 -m unittest)
hw/                hardware budget, board notes, hardware reviews
hwtest/            measurement scripts run on the board with mpremote
backups/           copies of what was on the board before changes
pm/                decision requests (inbox), rulings (outbox), decision log, status
UPLOAD.md          what to upload to the board, in order
CLAUDE.md          rules for the AI developer sessions working in this repo
```

## Running the tests

Game logic never imports `machine`, so it runs on a normal computer:

```bash
python3 -m unittest discover -s tests
```

## Getting code onto the board

Open Viper IDE (a web IDE, works in Chrome over WebSerial), connect to the board and upload the files listed in [`UPLOAD.md`](UPLOAD.md). To go back to the old program, upload `main_monolith.py` as `main.py`.

Only one program can use the board's USB connection at a time. Disconnect Viper before using `mpremote` from the terminal.

## How the project is run

Four roles, one repo:

| Role | Who | Does |
|---|---|---|
| Owner | John | Makes the art, uploads to the board, approves decisions |
| PM | Claude session "The PM" | Routes decisions, keeps scope, records rulings |
| Senior dev | Claude session | Writes and tests the software, files decision requests |
| Microcontroller expert | Claude session | Measures what the board can do and reviews anything touching speed, memory, storage or power |

Decisions flow through files: the dev files `pm/inbox/DR-NNN-*.md` with one recommendation, the expert reviews hardware-related ones in `hw/reviews/`, the PM takes them to John and records the ruling in `pm/outbox/`. Details in [`pm/README.md`](pm/README.md).

## Art

Phase 1 needs 67 small images (cards, chips, a table, banners, icons). All sizes and names are in [`assets/ASSETS.md`](assets/ASSETS.md). The first step is four pilot files to prove the pipeline before the rest are made.

## Known problems in the old program (`main_monolith.py`)

Kept for reference. The rebuild replaces it, so these will not be fixed there.

- Slots jackpot is impossible (the win check can never be true) and the other odds are accidental.
- The "Off" menu item never highlights (`c == blue` should be `c = blue`).
- `print_status_message` calls a misspelled `prinstring` (unused, so it has not crashed).
- Poker is a stub, and pressing B before A crashes it.
- R/P/S has no player input.
- Points are not saved, and the screen flickers from full redraws.

## Credits

The display driver and font in `main_monolith.py` are adapted from Tony Goodhew's Waveshare 1.3" workout (August 2021). Waveshare datasheets and demo code are kept outside this repository.
