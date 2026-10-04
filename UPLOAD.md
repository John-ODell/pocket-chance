# Upload list

_Kept current by the senior dev. Upload in the order shown using Viper IDE, then run the test line._

**Last updated:** 2026-10-03

## Right now: nothing to upload for the game
The board still runs the old `main.py` (a copy is in `main_monolith.py`). Nothing in this repo changes what the board does.

## Optional board check (read-only, writes nothing)
Purpose: tell me which MicroPython firmware is on the board, how much flash space is free, and how much RAM is free. I need this to confirm the correct 16 MB firmware is installed.

1. In Viper IDE, open `tools/board_probe.py` from this repo.
2. Run it on the board. Do **not** save it to the board.
3. Copy the printed output into a message or into `pm/` for me.

Test line: it should end with `--- done ---`. `flash total` should be close to 16,000 KB (or about 4,000 KB for a 4 MB board). If it shows about 1,400 KB, the board has firmware built for 2 MB and needs the RP2040-Plus firmware from micropython.org before we load art.

## Later (not yet written)
Planned board layout, pending DR-001: `/lib` for shared modules, `/games` for the games, `/assets` for converted images. The new program will be uploaded as `/pocket.py`, not `/main.py`, so the old program keeps working.

## Restore the old version
Upload `main_monolith.py` and name it `main.py` on the board.
