# DR-020: Slots: how the reels spin and stop

- **Status:** pending, **revision 2** (2026-10-05). Revision 1 was measured by the expert (hw/reviews/HR-020.md) and did not fit: 82 ms per frame instead of my 20 ms estimate. This revision is the measured design with the expert's four limits built in. The idea (scroll the real strip inside each window) is unchanged; the draw path is.
- **Filed by:** senior dev
- **Date:** 2026-10-04, revised 2026-10-05
- **Blocks:** Slots screen
- **Needs HW review:** yes. Done: HR-020 (fits with limits 1 to 4 below), HR-F03 (the per-blit `os.stat` cost, fixed in `lib/art.py`).

## What changed since revision 1 and why
1. **Symbols live in RAM during a spin.** Revision 1 read both symbols of every reel from flash on every frame. The expert measured each `Assets.blit` at about 8 ms (an `os.stat` of 3.7 ms plus open and header read on LittleFS), so three reels cost 49 ms per frame in reads alone. Now a symbol is read from flash only when it scrolls into a window.
2. **The compose buffer is pushed straight to the panel.** Revision 1 copied the composed window into the framebuffer and used `show_rect`, 10 ms per reel. The compose already holds exactly the window's pixels, so it is written to the panel directly (new `LCD.show_buf`); the framebuffer is updated once when the reels stop.
3. **Reels are staggered** so their symbol changes fall on different frames: at most one flash read per frame.
4. No `os.stat`, `open`, `FrameBuffer()` construction or allocation inside the frame loop.

## The decision
How the three reels animate, in what order they stop, how long a spin takes, and how much RAM the animation may hold.

## Why it matters
This is the only continuous animation in the project. It must look smooth at 24 MHz SPI as well as 62.5 MHz, inside the RAM left after the framebuffer (about 83 KB free before the slots module loads, HR-020).

## Measured (HR-020, real driver and board, 8 px per frame, three reels moving)
| Design | 62.5 MHz | 24 MHz |
|---|---|---|
| Revision 1 as written | 82 ms, 12 fps | 90 ms, 11 fps |
| **This revision** (symbols in RAM, direct push, staggered) | **13.1 ms, 76 fps** (max 14.3) | **17.7 ms, 56 fps** (max 28) |
| Frame on which one reel loads its next symbol | about 17 ms | about 22 ms |
| One reel moving (end of the spin) | 4.5 ms | |

## Options
### A. Two symbol slots per reel (6 slots, 37.6 KB) plus the 6,272-byte compose (recommended)
- Each reel keeps its current and next symbol in RAM; when the strip advances, the reel reads one new symbol (about 4 ms) into the slot that just scrolled out. With staggering, the worst frame is about 17 ms at 62.5 MHz, 22 ms at 24 MHz: no visible judder.
- RAM: 43.9 KB for the whole animation, allocated once when the slots screen starts and freed on exit (the module is dropped like blackjack). The expert measured 82.9 KB free before the slots module; estimate 5 KB for the module, leaving about 34 KB free during a spin. That is enough for the paytable screen text and the result, but it is the tightest RAM point in the project, so the expert's first bench of the real screen should report `gc.mem_free()` during a spin.
- Cons: the most RAM of the options.

### B. Two slots shared by all three reels (12.5 KB) plus the compose, 19 KB total
- Pros: 25 KB less RAM.
- Cons: on the frame where symbols change all three reels must re-read (six reads, 38 ms measured), once every seven frames at 8 px per frame: a visible judder.

### C. One full strip image per reel in RAM
- 32 symbols x 6,272 bytes = 200 KB. Does not fit. Rejected.

## Motion and timing (unchanged from revision 1)
- Full speed 8 px per frame (one symbol every 7 frames), aiming at 50 fps with a sleep to even out the frame time, slowing to 2 px per frame over the last symbol, then snapping to the stop position.
- Reels stop left to right, 0.35 s apart. A spin takes about 1.6 s (left reel) to 2.3 s (right reel). Keys are ignored while spinning.
- When the last reel stops, the three windows are drawn into the framebuffer once (so later band redraws show the right symbols), then the win is evaluated (DR-021).
- The design floor stays 20 fps: the game is fine if a frame ever takes 50 ms.

## Recommendation
Option A. The RAM is the price of a smooth spin and it is only held while the slots screen is open. If the first bench shows less than about 20 KB free during a spin, I switch to B with 4 px per frame (which halves the judder) and say so, without a new request.

## What John would have to do or accept
Nothing. Spins take about two seconds. `sym_blur` stays dropped from the art list.

## Appendix
HR-020 numbers: `os.stat` 3.7 ms; open and read of one 6,276-byte symbol 4.1 ms; two keyed blits from RAM into the compose 2.9 ms; direct push of a 56 x 56 window 1.5 ms. Scripts `hwtest/slots_spin_bench.py` (revision 1) and `hwtest/slots_spin_bench2.py` (this revision). Driver addition: `LCD.show_buf(x, y, w, h, buf)` pushes a prepared buffer to a window without touching the framebuffer.
