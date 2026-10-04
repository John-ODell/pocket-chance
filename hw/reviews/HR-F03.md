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

## Re-measured after the fix (step 1f `art.py`, 2026-10-04, `hwtest/blit_bench.py`)
| Operation | Before | After |
|---|---|---|
| 40x56 card blit from flash, first call (stat + header, cached from then on) | ~8.0 ms | 8.5 ms |
| **Same card, later calls** | ~8.0 ms | **5.6 ms** |
| `Assets.load` (open + read one 4,480-byte sprite into a buffer) | | 3.9 ms |
| `background_rows`, 48 rows, first / cached | | 9.6 / 6.7 ms |
| `LCD.show_buf`, 56x56 | | 1.9 ms |
| Code-drawn card (for comparison) | 3.9 ms | 3.9 ms |

Option A worked as designed (`os.stat` gone, ~3 ms saved), but `open()` itself costs about 3 ms on this LittleFS, so **a card from flash is still 5.6 ms, slower than the 3.9 ms code-drawn card**. For slots this no longer matters (symbols live in RAM during a spin, HR-020). For blackjack card art it does: a result scene with eight cards would be ~45 ms of blits where the code-drawn version is ~31 ms. The remedy is option C: one file per sprite sheet (`cards.565` holding all 52 faces and the back), opened once per scene, `seek` + `readinto` per card, which the read speed puts at ~1 ms per card plus ~1 ms for the keyed blit. That is a converter and `ASSETS.md` change, so it needs a decision request before John makes the card art.
