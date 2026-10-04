# DR-007: How the bankroll is saved to flash: file format and location

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-03
- **Blocks:** Bankroll module (lib/bankroll.py)
- **Needs HW review:** yes

## The decision
The file name, contents and write method used to keep the player's chips between power cycles.

## Why it matters
If power is cut while writing, the player could lose their chips. Writing too often wears the flash (it is rated for roughly 100,000 erases per block; the filesystem spreads writes, so this is not a practical worry at one write per round).

## Options
### A. One small text file, `/save.json`, written safely (recommended)
- What it is: JSON like `{"v":1,"bank":1000,"chk":1234}`. `v` is a format version so it can grow, and `chk` is a simple checksum of the other fields. It is written to `/save.tmp` first, then renamed over `/save.json`. The rename is atomic on the board's filesystem, so a power cut leaves either the old file or the new one.
- Written once per finished round, not on every button press.
- Pros: readable, `json` is built into MicroPython, easy to extend (stats, settings).
- Cons: slightly larger than a binary file (about 40 bytes). Irrelevant here.

### B. Raw 8-byte binary record
- Pros: tiny.
- Cons: not readable, harder to extend and debug.

### C. A save per game
- Cons: more files for nothing. One bankroll is shared.

## Recommendation
Option A. What happens if it is damaged is a separate request (DR-008).

## What John would have to do or accept
A `/save.json` file will appear on the board. Deleting it resets the bankroll.
