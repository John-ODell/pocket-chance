# Handoff: end of day 1 (2026-10-03)

Written by the PM so tomorrow starts from the repo, not from memory. Read this first, then `pm/STATUS.md`.

## What exists
- **Team:** John (owner), the PM, a senior dev session and a microcontroller expert session. Rules are in `CLAUDE.md`, `docs/roles/ENGINEER.md` and `pm/README.md`.
- **Dev work:** a tested blackjack rules engine, bankroll and table logic (58 tests, `python3 -m unittest discover -s tests`), a house-edge simulator (`tools/bj_edge.py`) and 14 decision requests (`pm/inbox/`).
- **Expert work:** measurement scripts in `hwtest/`, measured numbers in `hw/BUDGET.md`, and hardware reviews HR-001, 002, 003, 005, 006, 007, 008 and HR-F01 in `hw/reviews/`.
- **Nothing new runs on the board yet.** The board runs the old program, restored from backup.

## Board state (changed today)
- Reflashed by John to **MicroPython v1.29.0, Waveshare RP2040-Plus 16 MB** (file in `backups/firmware/`, not committed). The filesystem went from 1.4 MB to **15 MB**.
- `main.py` restored from `backups/2026-10-03/main.py`. It is byte-identical to `main_monolith.py`. The old menu runs.
- **Regression found:** the SPI (screen) clock now tops out at **24 MHz**, not 62.5 MHz, so a full-screen redraw takes about 46 ms (21 fps) instead of 18.5 ms (44 fps). **Diagnosed and fixed by the expert:** v1.29.0 clocks the peripherals from the 48 MHz USB PLL. A 3-line register fix measured back to **17.2 ms per full frame (58 fps)**. It is written up in `hw/BUDGET.md` with a before/after table. It is **not adopted yet**: it needs a decision request from the dev (touches low-level clock registers) before it goes into the game code. The register stays in the fixed state until the board is unplugged, which is harmless.
- Viper IDE can reconnect. Only one program can use the board's USB port at a time.

## Decisions
- **Approved by John:** DR-004, 009, 010, 011, 012, 013, 014 (rules and Pillow). See `pm/DECISIONS.md` and `pm/outbox/`.
- **Done at John's request:** the reflash from HR-F01 option A.
- **Not yet ruled (expert says all fit, HR-005 fits with limits):**

| Request | Topic | Dev's recommendation |
|---|---|---|
| DR-001 | File layout; new program uploaded as `/pocket.py`, old `main.py` keeps booting | A |
| DR-002 | Converted image file format (`.565`, raw, transparent key magenta) | B |
| DR-003 | Colour byte order (big-endian, no swap on load), gated on a screen check | A + gate |
| DR-005 | Streaming images from flash | A, limits in HR-005 |
| DR-006 | Keep art sizes; make 4 pilot images first | A |
| DR-007 | Bankroll save format and location | A |
| DR-008 | What happens on a damaged save | B |

## Update 2026-10-04 (morning)
- Screen check passed: left half red (big-endian RGB565), upright landscape. Pin map verified on the board, zero bounce. The 62.5 MHz fast-SPI fix looks clean on the panel and is adopted (DR-015).
- All 15 decision requests are ruled (`pm/outbox/`, `pm/DECISIONS.md`). John also ordered the old `main.py` erased from the board (D-003, backup verified by hash). The board is blank and boots to a dark screen. v1.29.0, 15 MB free.
- The dev is building the on-board modules, the converter and the blackjack screens. New entry installs as `/pocket.py`.
- Still unconfirmed: which physical button (top to bottom) is A, B, X and Y.

## Next
1. Dev delivers the converter and a pilot board test (`UPLOAD.md`). The expert reviews any new on-board module before John uploads it.
2. John makes the four pilot images (`c_AS`, `c_back`, `chip_5`, a small `table`), then the rest of the Phase 1 art if the pilot passes.
3. John uploads via Viper IDE (the expert must not hold the port at the same time).
