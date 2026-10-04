# HR-F02: Finding. `pocket.py` cannot start as uploaded: the `/assets` folder shadows `lib/assets.py`

- **Raised by:** microcontroller expert, 2026-10-04, bench check of UPLOAD.md step 1 on the board (firmware v1.29.0)
- **Type:** finding, blocks step 1 of `UPLOAD.md`. One-line fix for the dev; nothing for John to decide beyond accepting a module rename.
- **Severity:** the game does not start. Found before John uploaded anything.

## STATUS: FIXED and verified on the board, 2026-10-04
The dev renamed `lib/assets.py` to `lib/art.py` (commit `0ed9a55`) and added a test that fails if any module is ever named like a board folder. Re-bench with the 13 files exactly as `UPLOAD.md` lists them, from a power-cycled board with the empty `/assets` folder present, **no `sys.path` change**: all imports resolve, 8 scripted hands played with no errors (`hwtest/pocket_bench.py`). Numbers from the re-bench are in `hw/BUDGET.md`.

## What happens (original finding)
With the 13 files in place exactly as `UPLOAD.md` lists them, running `/pocket.py` stops at line 29:

```
  File "pocket.py", line 29, in <module>
ImportError: no module named 'assets.Assets'
```

## Why
`sys.path` on the board is `['', '.frozen', '/lib']`. `''` is the current directory, the root. MicroPython v1.29.0 treats a bare directory as a package (namespace package, no `__init__.py` needed), so `import assets` finds the empty **`/assets` folder** first and never looks in `/lib/assets.py`. `from assets import Assets` then fails because the folder has no `Assets`. Verified on the board:

```
import assets  ->  <module 'assets'>  (no __file__: it is the directory)
sys.path.insert(0, '/lib'); import assets  ->  <module 'assets' from '/lib/assets.py'>, has Assets
```

The CPython tests never see this because nothing creates an `assets` directory on the Mac's import path. `tools/pilot_test.py` has the same import and fails the same way.

## Fix options for the dev
### A. Rename the module (recommended)
`lib/assets.py` → something that is not also a folder name, for example `lib/art.py` or `lib/images.py`. Update the three imports (`pocket.py`, `games/blackjack.py`, `tools/pilot_test.py`) and the row in `UPLOAD.md`. Nothing else changes; the `/assets` folder stays as ruled in DR-001.

### B. Reorder `sys.path` in `pocket.py`
`sys.path.insert(0, '/lib')` before the imports. Works (that is how the rest of this bench ran), but it is a trap for the next person and would also have to go in `pilot_test.py` and anything run from Viper.

### C. Rename the folder
Would reopen DR-001 and `UPLOAD.md` for no gain.

## Bench results with the workaround in place (option B, applied only in `hwtest/pocket_bench.py`)
Eight hands of blackjack played with scripted keys, no errors. Numbers are in `hw/BUDGET.md` under "First on-board code" and summarised here (62.5 MHz SPI, code-drawn felt and cards, no art files):

| Path | Time |
|---|---|
| `draw_all` (scene change, full redraw + `show`) | 39–43 ms |
| bet change (`draw_top` + 24-row band) | 15 ms |
| hit / stand (`draw_player` + `draw_bottom` + 142-row band) | 29 ms |
| `finish_round` (save + `draw_all`) | 121 ms mean, **177 ms max** |
| save alone (tmp, old → `.bak`, tmp → json) | 54 ms mean, 102 ms max |
| RAM free after LCD / after all imports / after 8 hands | 101,104 / 84,272 / 64,576 bytes |

All within budget. Two notes for the dev, not blockers: (1) the scaled font is the Python cost: about 25 ms of the 43 ms `draw_all` is drawing, most of it size-2 text; (2) `finish_round` saves **before** redrawing, so the result banner appears up to 177 ms after the last key. Drawing first and saving after would make the result feel instant at no cost.
