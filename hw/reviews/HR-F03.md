# HR-F03: Finding. `Assets.blit` pays ~8 ms of filesystem overhead per sprite, before reading a pixel

- **Raised by:** microcontroller expert, 2026-10-04, while measuring DR-020 (`hwtest/slots_spin_bench.py`, `slots_spin_bench2.py`)
- **Type:** finding, for the dev. Not a blocker for blackjack; a blocker for any per-frame sprite animation (slots) and a free speed-up for card art.

## What I measured
On this board's LittleFS (v1.29.0, 15 MB filesystem, a handful of files):

| Operation | Time |
|---|---|
| `os.stat(path)` | **3.7 ms** |
| `open(path, 'rb')` + read 4-byte header + `readinto` 6,272 bytes | 4.1 ms |
| of which the actual flash read | ~1.1 ms (5.6 MB/s, `BUDGET.md`) |
| `Assets.blit` of one 56x56 sprite, all in | **~8 ms** |
| the same sprite blitted from RAM | 1.5 ms (keyed), 0.8 ms (no key) |

`lib/art.py` `_open()` does `os.stat` (for the length check), `open`, header read, then the pixel read, on **every** `blit` and `background_rows` call. Directory lookups on LittleFS are not cheap and they scale with the number of files in the folder, so this will get slower, not faster, as John's 60 assets arrive.

## Consequences
- Slots option A as described: six blits per frame = 48 ms of overhead per frame (HR-020).
- Blackjack with card art: a result scene blits ~8 cards and a banner = ~70 ms of overhead on top of the drawing, so card art would make the result *slower* than the code-drawn cards it replaces (3.9 ms each) unless this is fixed.
- Menu: 2 slice reads per joystick move = ~8 ms of the measured 46 ms.

## Fix options for the dev
### A. Cache the header check (recommended, small)
On the first successful open of a name, remember `(w, h, byte_offset)` in a dict; afterwards skip `os.stat` and the header read and go straight to `open` + `seek` + `readinto`. Saves ~4–5 ms per blit. The length check still happens once per asset per boot, which is all DR-002 asked for.

### B. Keep hot sprites in RAM (for animation only)
What HR-020 requires for the spin: read a sprite once, blit from RAM per frame (1.5 ms). Not a general policy, RAM is 60–80 KB in play.

### C. One open file per sprite sheet
Pack all symbols (or all cards) into one file and `seek`; one `open` per scene instead of one per sprite. Bigger change to the converter and `ASSETS.md`; not needed if A and B are done.

## Recommendation
A now (a few lines in `art.py`, no ruling needed beyond the PM's nod since it changes no format), B for slots as HR-020 says. I will re-measure a card blit once A is in.
