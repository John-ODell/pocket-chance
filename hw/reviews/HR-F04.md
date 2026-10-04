# HR-F04: Finding. Step 1h (sprite sheets) cut free RAM by 11 KB at boot and 23 KB mid-spin

- **Raised by:** microcontroller expert, 2026-10-04, bench check of `UPLOAD.md` step 1h before John saw it
- **Type:** finding, blocks step 1h going to John until trimmed. Verdict on the build as uploaded: **does not fit** the dev's own alarm line (mid-spin free under 20 KB).
- Method: the real program run end to end with scripted keys (`hwtest/pocket_scripted.py` + `hwtest/fakes/buttons.py`), John's save snapshotted and restored, nothing else loaded. Same method as the step 1g figures, so the comparison is clean. No sheet files on the board, so every path took the code-drawn fallback.

## Numbers
| Point | Step 1g | **Step 1h** | Change |
|---|---|---|---|
| Boot, menu up | 75,920 | **65,072–65,584** | **−10.5 KB** |
| After `import slots` (module + Screen) | 46,496 | 36,880–37,248 | −9.3 KB |
| Slots ready, after `gc.collect()` | | 32,608 | |
| **Mid-spin (game's own print, no gc)** | 36,432 | **9,488–12,992** | **−23 KB** |
| After a spin, before / after `gc.collect()` | | 22,544 / 28,448 | garbage **5.9 KB per spin** |
| After spin 2 / spin 3, after gc | | 29,040 / 28,496 | **stable: no leak** |
| Back at the menu, after gc | 67,328 | 58,480 | −8.8 KB |
| Blackjack `draw_all` / key→banner (`pocket_bench.py`) | 44.6 / 86 ms | 46.5 / 91 ms | +2 / +5 ms |

In my heavier bench harness (`slots_play_bench.py`) the slots `Screen` could no longer allocate its three 6,272-byte window buffers at all; that harness carries ~29 KB of its own, but it shows how close the real program now runs to the edge.

## Reading
1. **About 11 KB went to code at boot.** `art.py` grew from 5.1 to 8.3 KB of source, `sheets.py` is new and builds `_MEMBER`, a dict of 75 name → tuple entries, at import (roughly 3–4 KB of heap kept for the life of the program), and `blackjack.py`, `slots.py`, `pocket.py` each grew. Bytecode and constants live in RAM on this port.
2. **The spin makes ~6 KB of garbage per spin and keeps ~4 KB after the first.** Nothing leaks: three spins end at the same free figure after collection. But the game's "mid-spin mem_free" reads garbage as used, which is why it shows 9–12 KB. MicroPython collects automatically when an allocation fails, so the practical risks are (a) a collection pause landing inside the 20 ms frame budget, and (b) fragmentation making a 6,272-byte buffer unobtainable on a later scene change. Risk (b) is what my harness hit.
3. **Timing moved +2 to +5 ms** on blackjack scenes, consistent with each scene probing for sheets that are not there (`use_sheets` → `_open` → `os.stat` 3.7 ms on the first probe per name per boot, then cached as missing). Small, but not zero as DR-024 assumed.

## The gc pause, measured in the slots state
`gc.collect()` with slots loaded takes **28.3–29.1 ms** (20.8 ms at the menu). The spin frame budget is 20 ms. So if the ~7 KB of garbage a spin produces triggers MicroPython's automatic collection while the reels move, the animation freezes for about a frame and a half, visibly. On this build that is likely: the spin starts with ~28 KB free and makes 7 KB of garbage against a heap that also holds transients. This turns "collect before the reels start and allocate nothing during them" from advice into a requirement for a smooth spin.

## What would fix it (for the dev to choose)
- **`gc.collect()` once right before the reels start** (after the stake is drawn). Costs a few ms once per spin, outside the animation, and the spin then starts from ~28 KB clean instead of inheriting the result-screen garbage. Cheapest single change.
- **Trim import-time RAM in `sheets.py`:** do not build `_MEMBER` at import; derive (sheet, index) on demand from the five tuples (a linear scan of 75 names once per scene entry, cached per scene), or store members as one string per sheet and `split()` lazily. Expect 3–4 KB back.
- **Find the per-spin allocations.** Candidates: `memoryview(buf)[:n]` slices in `Sheet.read/rows` and `Assets.load` (one small object each call), the `plan` object and its lists, string formatting for the result line, `_from_sheet` tuples. Each is small; together they are the 6 KB. HR-020 limit 4 was "no allocation in the frame loop".
- **Redefine the alarm metric** so it means what the dev wants: free RAM *after* `gc.collect()` at spin end (≥ 20 KB) and the largest allocatable block at scene entry (≥ 6,272 B), not the instantaneous mid-spin reading.
- Precompiling to `.mpy` would remove the compiler's peak at import but not the bytecode's resident size; not a fix for this.

## Board state
Step 1h is on the board and not shown to John. Previous good build (step 1g + the `open_sprite` `art.py`) is in `backups/2026-10-04-board-8/` (art.py, blackjack.py, slots.py, pocket.py); rollback is five file copies if the PM asks.
