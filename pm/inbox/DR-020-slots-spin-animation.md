# DR-020: Slots: how the reels spin and stop

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-04
- **Blocks:** Slots screen
- **Needs HW review:** yes

## The decision
How the three reels animate, in what order they stop, how long a spin takes, and how it is drawn within the redraw budget.

## Why it matters
This is the only continuous animation in the project. It must look smooth at 24 MHz SPI and within the one 16 KB scratch buffer (DR-005).

## Options
### A. Scroll the real strip inside each 56 x 56 window, compose per window in scratch, push the three windows (recommended)
- Each frame, for every spinning reel: take the two strip symbols straddling the window (current and next), blit them at the scroll offset into a 56 x 56 scratch FrameBuffer (6,272 bytes; `blit` clips at the window edges so nothing bleeds onto the cabinet), copy that into the framebuffer at the window position, and push just that 56 x 56 window (`lcd.show_rect`). The symbol sprites are read from flash per frame (two 6,276-byte reads per reel, about 1.5 ms each).
- Scratch use: one 6,272-byte compose buffer plus one 6,276-byte sprite slot, both slices of the existing 16 KB scratch. No new allocation in the loop.
- My estimate per frame with three reels moving: 3 x (2 reads 3 ms + compose and copy ~2 ms + push ~1.5 ms at 62.5 MHz) = **about 20 ms, 40 to 50 fps cap at 62.5 MHz; about 30 ms at 24 MHz**. The expert should measure; I will design for 20 fps.
- Motion: 8 px per frame at full speed (one symbol every 7 frames), slowing to 2 px per frame over the last symbol, then snapping to the stop. Reels stop left to right, 0.35 s apart. Whole spin about 1.6 s (left reel) to 2.3 s (right reel). Keys are ignored while spinning.
- Cons: the most code of the three options.

### B. Flash random symbols in place (no scrolling)
- Pros: trivial, about 5 ms per frame.
- Cons: looks cheap; John asked for a slot machine feel.

### C. Full-band redraw per frame (restore the 56-row band from the cabinet art, blit 6 symbols, push the band)
- Cons: a 26 KB cabinet row read plus a 240 x 56 band push (~8 ms) every frame; about 30 ms at 62.5 MHz and 45 ms at 24 MHz. Slower than A for no gain.

## Recommendation
Option A. The `sym_blur` art becomes unnecessary and is dropped from the asset list (DR-023). If the expert measures A above 35 ms per frame at 24 MHz, I fall back to 4 px steps at the same frame rate, which only makes the spin longer.

## What John would have to do or accept
Nothing. Spins take about two seconds.

## Appendix
Measured reference points in `hw/BUDGET.md`: 48 x 48 window push 3.9 ms including Python; 40 x 56 sprite read ~1 ms; 240 x 48 band push 7.2 ms.
