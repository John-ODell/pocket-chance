# DR-001: Module layout under lib/ and games/, and the main.py structure

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-03
- **Blocks:** Everything except the pure rules engine (which is built already and may need to move)
- **Needs HW review:** yes

## The decision
How the new program is split into files, which folders they go in on the board, and what `main.py` does.

## Why it matters
Every later file, import and upload step follows from this. The RP2040 has little RAM, so the layout decides how much is loaded at once. John uploads by hand, so fewer and clearer files are better.

## Options
### A. Shared `lib/`, one flat module per game, thin `main.py` (recommended)
- What it is:
  - `lib/` holds shared code: `lcd.py` (display driver, from the monolith), `font.py`, `buttons.py` (joystick and buttons), `cards.py` (cards, shoe, hand value; pure), `assets.py` (loads art), `bankroll.py` (saved chips), `ui.py` (shared drawing helpers).
  - `games/` holds one module per game, for example `blackjack_rules.py` (pure) and `blackjack.py` (screens and input). Each game module exposes one function, `run(ctx)`.
  - `main.py` starts the hardware, loads the bankroll, shows the menu, and imports a game only when it is chosen. It drops the game module when you leave, which frees RAM.
- Pros: only the game being played sits in RAM. Pure logic and display code are separate files, so the logic can be tested on the Mac. Adding slots later means adding two files.
- Cons: more files for John to upload than one big file (about 12 for blackjack).
- Cost: low. The old driver and font get copied across; the old code stays untouched.

### B. Everything in the board's root folder
- Pros: no folder setup on the board.
- Cons: breaks the `lib/` and `games/` structure `CLAUDE.md` already describes, and gets messy with 60+ asset files.

### C. One package per game (`games/blackjack/rules.py`, `ui.py`)
- Pros: tidy as games grow.
- Cons: extra folders on the board and more import path work for little gain with only two games.

## Recommendation
Option A. Two details that follow from it:
- MicroPython's default import path includes `/lib` but not `/games`, so `main.py` adds `/games` to the path.
- Until John says otherwise, the new entry file goes to the board as `/pocket.py`, **not** `/main.py`, so the old working program keeps booting. Renaming it to `main.py` is a later step, taken only on John's say-so. Overwriting the boot file needs his approval.

## What John would have to do or accept
Create `/lib`, `/games` and `/assets` folders on the board (Viper IDE can do this). Upload files by folder as listed in `UPLOAD.md`.

## Appendix
Provisional locations already used (they will move if the ruling says so): `lib/cards.py`, `games/blackjack_rules.py`, tests in `tests/`.
